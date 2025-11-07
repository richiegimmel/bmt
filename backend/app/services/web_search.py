"""
Web search service for finding Kentucky statutes and legal information.
"""

import httpx
from typing import List, Dict, Any, Optional
import json
from urllib.parse import quote


class WebSearchService:
    """Service for searching web resources, particularly Kentucky statutes."""

    def __init__(self):
        """Initialize the web search service."""
        self.timeout = 10.0
        self.user_agent = "Board Management Tool Legal Assistant/1.0"

    async def search_kentucky_statutes(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for Kentucky statutes and legal information.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search results with title, url, and snippet
        """
        try:
            # Use DuckDuckGo's instant answer API for Kentucky statute searches
            # Format the query to focus on Kentucky law
            search_query = f"Kentucky statute {query} site:lrc.ky.gov OR site:legislature.ky.gov"

            results = await self._search_duckduckgo(search_query, limit)

            # If no results from official sites, try broader search
            if not results:
                search_query = f"Kentucky {query} law statute"
                results = await self._search_duckduckgo(search_query, limit)

            return results

        except Exception as e:
            print(f"Error in web search: {e}")
            return []

    async def _search_duckduckgo(
        self,
        query: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Perform a search using DuckDuckGo's HTML interface.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search results
        """
        try:
            # Use DuckDuckGo Lite (HTML) interface for simple scraping
            url = f"https://lite.duckduckgo.com/lite/"

            headers = {
                "User-Agent": self.user_agent
            }

            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # First, get the search page
                response = await client.post(
                    url,
                    data={"q": query},
                    headers=headers,
                    follow_redirects=True
                )

                if response.status_code != 200:
                    return []

                # Parse the HTML response (simple parsing)
                html = response.text
                results = self._parse_duckduckgo_html(html, limit)

                return results

        except Exception as e:
            print(f"DuckDuckGo search error: {e}")
            return []

    def _parse_duckduckgo_html(self, html: str, limit: int) -> List[Dict[str, Any]]:
        """
        Parse DuckDuckGo Lite HTML to extract search results.

        Note: This is a simple parser. For production, consider using BeautifulSoup
        or the official DuckDuckGo API.
        """
        results = []

        try:
            # Simple extraction using string parsing
            # Look for result links in the HTML
            lines = html.split('\\n')
            current_result = {}

            for line in lines:
                # Look for result links
                if '<a rel=' in line and 'http' in line:
                    # Extract URL
                    start = line.find('href="') + 6
                    end = line.find('"', start)
                    if start > 5 and end > start:
                        url = line[start:end]

                        # Extract title (text between >< in the link)
                        title_start = line.find('>', end) + 1
                        title_end = line.find('<', title_start)
                        if title_start > 0 and title_end > title_start:
                            title = line[title_start:title_end].strip()

                            if url and title and not url.startswith('//duckduckgo'):
                                current_result = {
                                    'title': title,
                                    'url': url,
                                    'snippet': ''
                                }

                # Look for snippets (following the link)
                elif current_result and '<td class="result-snippet"' in line:
                    # Get next few lines for snippet
                    snippet_start = line.find('>') + 1
                    snippet = line[snippet_start:].strip()
                    if snippet and snippet != '</td>':
                        current_result['snippet'] = snippet.replace('<b>', '').replace('</b>', '').replace('</td>', '')
                        results.append(current_result)
                        current_result = {}

                        if len(results) >= limit:
                            break

        except Exception as e:
            print(f"HTML parsing error: {e}")

        return results[:limit]

    def format_search_results_for_context(
        self,
        results: List[Dict[str, Any]]
    ) -> str:
        """
        Format search results for inclusion in AI context.

        Args:
            results: List of search results

        Returns:
            Formatted string for context
        """
        if not results:
            return "No web search results found."

        formatted = "Web Search Results:\\n\\n"

        for i, result in enumerate(results, 1):
            formatted += f"{i}. {result['title']}\\n"
            formatted += f"   URL: {result['url']}\\n"
            if result.get('snippet'):
                formatted += f"   {result['snippet']}\\n"
            formatted += "\\n"

        return formatted

    async def search_general(
        self,
        query: str,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Perform a general web search.

        Args:
            query: Search query
            limit: Maximum number of results

        Returns:
            List of search results
        """
        return await self._search_duckduckgo(query, limit)
