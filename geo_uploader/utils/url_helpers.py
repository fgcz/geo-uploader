from urllib.parse import urljoin, urlparse

from flask import request, url_for


class URLHelper:
    @staticmethod
    def is_safe_url(target: str) -> bool:
        """Extract your URL validation logic"""
        if not target:
            return False
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return (
            test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc
        )

    @staticmethod
    def get_safe_redirect_url(next_page: str | None = None) -> str:
        """Extract your redirect logic"""
        if next_page and URLHelper.is_safe_url(next_page):
            return next_page
        return url_for("main.index")
