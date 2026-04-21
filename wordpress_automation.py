"""
wordpress_automation.py

WordPress REST API client for automating blog post creation, scheduling,
categorization, tagging, and basic SEO metadata.

Authentication uses WordPress Application Passwords (WP 5.6+).
No extra dependencies beyond 'requests', which is already in requirements.txt.
"""

import mimetypes
import os
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime


class WordPressClient:
    """
    Thin wrapper around the WordPress REST API (v2).

    Usage::

        client = WordPressClient("https://example.com", "user", "xxxx xxxx xxxx")
        ok, msg = client.test_connection()
        post_id, msg = client.create_post(
            title="Hello World",
            content="<p>My first automated post.</p>",
            status="publish",
        )
    """

    def __init__(self, site_url: str, username: str, app_password: str):
        self.base_url = site_url.rstrip("/") + "/wp-json/wp/v2"
        self.auth = HTTPBasicAuth(username, app_password)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.session.headers.update({"Content-Type": "application/json"})

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def test_connection(self):
        """
        Verifies that the credentials are valid.

        Returns:
            (bool, str): (success, human-readable message)
        """
        try:
            response = self.session.get(f"{self.base_url}/users/me", timeout=15)
            if response.status_code == 200:
                data = response.json()
                return True, f"Connected as '{data.get('name', 'unknown')}'"
            return False, f"Auth failed (HTTP {response.status_code}): {response.text[:200]}"
        except requests.exceptions.ConnectionError:
            return False, "Could not reach the site. Check the URL and your internet connection."
        except Exception as exc:
            return False, f"Unexpected error: {exc}"

    # ------------------------------------------------------------------
    # Categories & Tags
    # ------------------------------------------------------------------

    def get_or_create_terms(self, taxonomy: str, names: list):
        """
        Resolves a list of term names to their WP IDs, creating missing ones.

        Args:
            taxonomy: 'categories' or 'tags'
            names:    List of term name strings.

        Returns:
            list[int]: List of WP term IDs.
        """
        ids = []
        for name in names:
            name = name.strip()
            if not name:
                continue
            # Search for existing term
            search_resp = self.session.get(
                f"{self.base_url}/{taxonomy}",
                params={"search": name, "per_page": 5},
                timeout=15,
            )
            if search_resp.status_code == 200:
                results = search_resp.json()
                matches = [t for t in results if t["name"].lower() == name.lower()]
                if matches:
                    ids.append(matches[0]["id"])
                    continue
            # Create it
            create_resp = self.session.post(
                f"{self.base_url}/{taxonomy}",
                json={"name": name},
                timeout=15,
            )
            if create_resp.status_code in (200, 201):
                ids.append(create_resp.json()["id"])
        return ids

    # ------------------------------------------------------------------
    # Posts
    # ------------------------------------------------------------------

    def create_post(
        self,
        title: str,
        content: str,
        status: str = "draft",
        categories: list = None,
        tags: list = None,
        seo_description: str = "",
        scheduled_at: datetime = None,
        excerpt: str = "",
    ):
        """
        Creates or schedules a WordPress post.

        Args:
            title:           Post title.
            content:         Post body (HTML or plain text).
            status:          'publish', 'draft', or 'future' (scheduled).
            categories:      List of category name strings.
            tags:            List of tag name strings.
            seo_description: Stored as the post excerpt (visible to SEO plugins).
            scheduled_at:    datetime for scheduled posts (status='future').
            excerpt:         Short summary; falls back to seo_description.

        Returns:
            (int or None, str): (post_id or None, human-readable result message)
        """
        category_ids = self.get_or_create_terms("categories", categories or [])
        tag_ids = self.get_or_create_terms("tags", tags or [])

        payload = {
            "title": title,
            "content": content,
            "status": status,
            "categories": category_ids,
            "tags": tag_ids,
            "excerpt": excerpt or seo_description,
        }

        if status == "future" and scheduled_at:
            # WP requires ISO 8601 local time (no timezone suffix for "future")
            payload["date"] = scheduled_at.strftime("%Y-%m-%dT%H:%M:%S")

        try:
            response = self.session.post(
                f"{self.base_url}/posts", json=payload, timeout=30
            )
            if response.status_code in (200, 201):
                post = response.json()
                post_id = post.get("id")
                post_link = post.get("link", "")
                return post_id, f"Post created (ID {post_id}): {post_link}"
            return None, f"Failed to create post (HTTP {response.status_code}): {response.text[:300]}"
        except Exception as exc:
            return None, f"Error creating post: {exc}"

    # ------------------------------------------------------------------
    # Media upload
    # ------------------------------------------------------------------

    def upload_media(self, file_path: str, alt_text: str = ""):
        """
        Uploads an image or file as a WordPress media item.

        Args:
            file_path: Absolute path to the local file.
            alt_text:  Alt text for images.

        Returns:
            (int or None, str): (media_id or None, message)
        """
        mime_type, _ = mimetypes.guess_type(file_path)
        if not mime_type:
            mime_type = "application/octet-stream"

        filename = os.path.basename(file_path)
        try:
            with open(file_path, "rb") as fh:
                headers = {
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Type": mime_type,
                }
                # Session auth is already set; override Content-Type for binary upload
                response = self.session.post(
                    f"{self.base_url}/media",
                    data=fh,
                    headers=headers,
                    timeout=60,
                )
            if response.status_code in (200, 201):
                media = response.json()
                media_id = media.get("id")
                if alt_text:
                    self.session.post(
                        f"{self.base_url}/media/{media_id}",
                        json={"alt_text": alt_text},
                        timeout=15,
                    )
                return media_id, f"Media uploaded (ID {media_id}): {media.get('source_url', '')}"
            return None, f"Media upload failed (HTTP {response.status_code}): {response.text[:300]}"
        except Exception as exc:
            return None, f"Error uploading media: {exc}"
