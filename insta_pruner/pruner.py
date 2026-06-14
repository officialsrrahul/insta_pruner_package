"""
pruner.py
---------
Core Pruner class for the insta_pruner package.
"""

import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager


class Pruner:
    """
    Pruner connects to your already-open, logged-in Chrome browser and
    processes a list of Instagram usernames (typically non-followers),
    unfollowing those that don't meet your criteria.

    Parameters
    ----------
    usernames_file : str, optional
        Path to a .txt file containing one Instagram username per line.
        Lines starting with # are treated as comments and ignored.
    usernames : list, optional
        A list of Instagram usernames to process directly.
        If both usernames_file and usernames are provided, usernames takes priority.
    threshold : int, optional
        Follower count threshold. Accounts with >= this many followers are
        treated as influencers and kept. Default is 5000.
    inactive_months : int, optional
        Number of months of inactivity (no posts or reels) after which an
        account is unfollowed. Default is 6.
    unfollowed_log : str, optional
        Path to the file where unfollowed accounts are logged. Default is 'unfollowed.txt'.
    kept_log : str, optional
        Path to the file where kept accounts are logged. Default is 'kept_following.txt'.
    debugging_port : int, optional
        Chrome remote debugging port. Must match the port Chrome was launched with.
        Default is 9222.
    pause_before_check : int, optional
        Seconds to wait for a profile page to load before reading data. Default is 4.
    pause_between_users : int, optional
        Seconds to wait between processing each user. Default is 2.

    Examples
    --------
    Using a file:
        from insta_pruner import Pruner
        pruner = Pruner(usernames_file="non_followers.txt", threshold=5000)
        pruner.run()

    Using a list:
        from insta_pruner import Pruner
        pruner = Pruner(usernames=["user1", "user2"], threshold=3000, inactive_months=3)
        pruner.run()
    """

    INSTAGRAM_BASE_URL = "https://www.instagram.com/"

    def __init__(
        self,
        usernames_file: Optional[str] = None,
        usernames: Optional[list] = None,
        threshold: int = 5000,
        inactive_months: int = 6,
        unfollowed_log: str = "unfollowed.txt",
        kept_log: str = "kept_following.txt",
        debugging_port: int = 9222,
        pause_before_check: int = 4,
        pause_between_users: int = 2,
    ):
        if usernames is None and usernames_file is None:
            raise ValueError("Provide either 'usernames' list or 'usernames_file' path.")

        self.usernames_file     = usernames_file
        self._usernames_input   = usernames
        self.threshold          = threshold
        self.inactive_months    = inactive_months
        self.unfollowed_log     = unfollowed_log
        self.kept_log           = kept_log
        self.debugging_port     = debugging_port
        self.pause_before_check = pause_before_check
        self.pause_between_users = pause_between_users

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Start the pruning process. Chrome must already be open and logged in."""
        usernames = self._load_usernames()
        if not usernames:
            print("No usernames to process.")
            return

        total = len(usernames)
        print(f"Insta Pruner started.")
        print(f"Accounts to check : {total}")
        print(f"Threshold         : {self.threshold:,} followers")
        print(f"Inactive after    : {self.inactive_months} months")
        print(f"Connecting to Chrome on port {self.debugging_port}...\n")

        driver = self._create_driver()
        print("Connected! Starting...\n")

        self._init_log_files()

        for idx, username in enumerate(usernames, start=1):
            print(f"[{idx}/{total}] @{username}")
            self._process_user(driver, username)
            if idx < total:
                print(f"   Waiting {self.pause_between_users}s...")
                time.sleep(self.pause_between_users)

        print(f"\nAll done!")
        print(f"  \u21b3 Unfollowed : {self.unfollowed_log}")
        print(f"  \u21b3 Kept       : {self.kept_log}")

    # ------------------------------------------------------------------
    # Private — setup
    # ------------------------------------------------------------------

    def _load_usernames(self) -> list:
        if self._usernames_input is not None:
            return [u.lstrip("@").strip() for u in self._usernames_input if u.strip()]
        path = Path(self.usernames_file)
        if not path.exists():
            print(f"ERROR: '{self.usernames_file}' not found.")
            return []
        with open(path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        return [
            line.strip().lstrip("@")
            for line in lines
            if line.strip() and not line.strip().startswith("#")
        ]

    def _create_driver(self) -> webdriver.Chrome:
        options = Options()
        options.add_experimental_option("debuggerAddress", f"127.0.0.1:{self.debugging_port}")
        service = Service(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    def _init_log_files(self) -> None:
        run_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for filepath, title in [
            (self.unfollowed_log, "UNFOLLOWED ACCOUNTS"),
            (self.kept_log,       "KEPT FOLLOWING ACCOUNTS"),
        ]:
            path = Path(filepath)
            file_exists_with_content = path.exists() and path.stat().st_size > 0
            with open(filepath, "a", encoding="utf-8") as f:
                if file_exists_with_content:
                    f.write("\n")
                    f.write("# " + "=" * 75 + "\n")
                    f.write(f"# NEW RUN \u2014 {run_time}\n")
                    f.write("# " + "=" * 75 + "\n")
                else:
                    f.write(f"# {title}\n")
                    f.write("# " + "=" * 75 + "\n")
                    f.write(f"# Run started {run_time}\n")
                    f.write("# " + "=" * 75 + "\n")
                f.write(f"# {'username':<25} {'followers':>10}  {'last_active':<12}  reason\n")
                f.write("# " + "-" * 75 + "\n")
                f.flush()

    # ------------------------------------------------------------------
    # Private — logging
    # ------------------------------------------------------------------

    def _log_entry(
        self,
        filepath: str,
        username: str,
        followers: Optional[int],
        last_active: Optional[datetime],
        reason: str,
    ) -> None:
        followers_str  = f"{followers:,}" if followers is not None else "N/A"
        last_active_str = last_active.strftime("%Y-%m-%d") if last_active else "N/A"
        line = f"@{username:<25} {followers_str:>10}  {last_active_str:<12}  {reason}\n"
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(line)
            f.flush()

    # ------------------------------------------------------------------
    # Private — Instagram data reading
    # ------------------------------------------------------------------

    def _parse_follower_count(self, text: str) -> Optional[int]:
        text = text.strip().replace(",", "")
        if not text or not text[0].isdigit():
            return None
        try:
            if text.upper().endswith("M"):
                return int(float(text[:-1]) * 1_000_000)
            if text.upper().endswith("K"):
                return int(float(text[:-1]) * 1_000)
            digits = re.sub(r"[^\d]", "", text)
            return int(digits) if digits else None
        except (ValueError, OverflowError):
            return None

    def _get_follower_count(self, driver: webdriver.Chrome) -> Optional[int]:
        try:
            meta = driver.find_element(By.XPATH, "//meta[@property='og:description']")
            content = meta.get_attribute("content") or ""
            match = re.search(r"([\d,\.]+[KkMm]?)\s+Followers", content)
            if match:
                result = self._parse_follower_count(match.group(1))
                if result is not None:
                    return result
        except NoSuchElementException:
            pass
        try:
            spans = driver.find_elements(By.XPATH, "//a[contains(@href,'/followers/')]//span")
            for span in spans:
                for raw in [span.get_attribute("title") or "", span.text or ""]:
                    result = self._parse_follower_count(raw)
                    if result is not None:
                        return result
        except NoSuchElementException:
            pass
        try:
            match = re.search(r'"edge_followed_by":\{"count":(\d+)\}', driver.page_source)
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return None

    def _read_date_from_content_page(
        self,
        driver: webdriver.Chrome,
        content_url: str,
        profile_url: str,
        label: str,
    ) -> Optional[datetime]:
        print(f"   Opening first {label} to read date...")
        driver.get(content_url)
        time.sleep(3)
        try:
            time_el = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.XPATH, "//time[@datetime]"))
            )
            dt_str = time_el.get_attribute("datetime")
            result = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            driver.get(profile_url)
            time.sleep(3)
            return result
        except (TimeoutException, ValueError):
            driver.get(profile_url)
            time.sleep(3)
            return None

    def _get_last_activity_date(
        self, driver: webdriver.Chrome, profile_url: str
    ) -> Optional[datetime]:
        try:
            driver.execute_script("window.scrollBy(0, 700);")
            time.sleep(2)
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        except Exception:
            pass

        try:
            time_els = driver.find_elements(By.XPATH, "//time[@datetime]")
            if time_els:
                dt_str = time_els[0].get_attribute("datetime")
                return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            pass

        dates = []

        try:
            post_el = driver.find_element(By.XPATH, "//a[contains(@href,'/p/')]")
            post_url = post_el.get_attribute("href")
            if post_url:
                d = self._read_date_from_content_page(driver, post_url, profile_url, "post")
                if d:
                    print(f"   Post date  : {d.strftime('%Y-%m-%d')}")
                    dates.append(d)
        except NoSuchElementException:
            pass

        try:
            reel_el = driver.find_element(By.XPATH, "//a[contains(@href,'/reel/')]")
            reel_url = reel_el.get_attribute("href")
            if reel_url:
                d = self._read_date_from_content_page(driver, reel_url, profile_url, "reel")
                if d:
                    print(f"   Reel date  : {d.strftime('%Y-%m-%d')}")
                    dates.append(d)
        except NoSuchElementException:
            pass

        if dates:
            return max(dates)

        try:
            matches = re.findall(r'"taken_at_timestamp":(\d+)', driver.page_source)
            if matches:
                latest_ts = max(int(ts) for ts in matches)
                return datetime.fromtimestamp(latest_ts, tz=timezone.utc)
        except Exception:
            pass

        return None

    # ------------------------------------------------------------------
    # Private — decision logic
    # ------------------------------------------------------------------

    def _should_unfollow(
        self, followers: Optional[int], last_active: Optional[datetime]
    ) -> tuple:
        if followers is None:
            return False, "\u26a0\ufe0f  Could not read follower count \u2014 skipping."
        cutoff        = datetime.now(timezone.utc) - timedelta(days=self.inactive_months * 30)
        low_followers = followers < self.threshold
        inactive      = (last_active is not None) and (last_active < cutoff)
        last_str      = last_active.strftime("%Y-%m-%d") if last_active else "unreadable"
        if low_followers and last_active is None:
            return True, f"followers < {self.threshold:,} | no posts/reels found"
        if low_followers and inactive:
            return True, f"followers < {self.threshold:,} | last active {last_str} (inactive)"
        if low_followers:
            return True, f"followers < {self.threshold:,}"
        if inactive:
            return True, f"last active {last_str} (inactive > {self.inactive_months}mo)"
        reasons = [f"followers {followers:,} \u2265 {self.threshold:,}"]
        if last_active:
            reasons.append(f"last active {last_str} is recent")
        return False, " | ".join(reasons)

    # ------------------------------------------------------------------
    # Private — unfollow action
    # ------------------------------------------------------------------

    def _js_click(self, driver: webdriver.Chrome, element) -> None:
        driver.execute_script("arguments[0].click();", element)

    def _click_unfollow(self, driver: webdriver.Chrome, username: str) -> bool:
        following_xpaths = [
            "//button[.//div[text()='Following']]",
            "//button[@aria-label='Following']",
            "//button[contains(.,'Following')]",
        ]
        clicked_following = False
        for xpath in following_xpaths:
            try:
                btn = WebDriverWait(driver, 8).until(EC.element_to_be_clickable((By.XPATH, xpath)))
                self._js_click(driver, btn)
                print("   Clicked 'Following' \u2014 waiting for menu...")
                clicked_following = True
                break
            except (TimeoutException, NoSuchElementException):
                continue

        if not clicked_following:
            print(f"   \u26a0\ufe0f  Could not find 'Following' button for @{username}.")
            return False

        time.sleep(2)

        unfollow_xpaths = [
            "//*[@role='dialog']//button[normalize-space(.)='Unfollow']",
            "//*[@role='dialog']//*[normalize-space(.)='Unfollow']",
            "//button[normalize-space(.)='Unfollow']",
            "//li[.//*[normalize-space(text())='Unfollow']]",
            "//*[normalize-space(text())='Unfollow']",
        ]
        for xpath in unfollow_xpaths:
            try:
                el = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.XPATH, xpath)))
                self._js_click(driver, el)
                print("   \u2705 Unfollowed!")
                time.sleep(1)
                return True
            except (TimeoutException, NoSuchElementException):
                continue

        try:
            for el in driver.find_elements(By.XPATH, "//*[normalize-space(.)='Unfollow']"):
                if (el.text or "").strip().lower() == "unfollow":
                    self._js_click(driver, el)
                    print("   \u2705 Unfollowed (brute force)!")
                    return True
        except Exception:
            pass

        print("   \u26a0\ufe0f  Could not click Unfollow in menu.")
        return False

    # ------------------------------------------------------------------
    # Private — per-user flow
    # ------------------------------------------------------------------

    def _process_user(self, driver: webdriver.Chrome, username: str) -> None:
        url = f"{self.INSTAGRAM_BASE_URL}{username}/"
        print(f"\n-> {url}")
        driver.get(url)
        print(f"   Waiting {self.pause_before_check}s for page to load...")
        time.sleep(self.pause_before_check)

        followers   = self._get_follower_count(driver)
        last_active = self._get_last_activity_date(driver, url)

        print(f"   Followers   : {followers:,}" if followers is not None else "   Followers   : N/A")
        print(f"   Last active : {last_active.strftime('%Y-%m-%d') if last_active else 'N/A (no posts or reels)'}")

        decision, reason = self._should_unfollow(followers, last_active)

        if decision:
            print(f"   \u2192 UNFOLLOW ({reason})")
            success = self._click_unfollow(driver, username)
            if success:
                self._log_entry(self.unfollowed_log, username, followers, last_active, reason)
            else:
                self._log_entry(self.kept_log, username, followers, last_active, f"unfollow failed: {reason}")
        else:
            print(f"   \u2192 KEEP ({reason})")
            self._log_entry(self.kept_log, username, followers, last_active, reason)
