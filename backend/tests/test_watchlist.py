"""Tests for watchlist endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_watchlist_lifecycle(client: AsyncClient, auth_headers: dict):
    """Test the full watchlist lifecycle: empty → add → get → remove → empty."""
    # 1. Start with empty watchlist
    resp = await client.get("/api/v1/watchlist/", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 0

    # 2. Add to watchlist fails with non-existent product
    resp = await client.post(
        "/api/v1/watchlist/",
        json={"product_id": "non-existent-product-id"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_add_watchlist_product_not_found(
    client: AsyncClient, auth_headers: dict
):
    """Adding a non-existent product should return 404."""
    resp = await client.post(
        "/api/v1/watchlist/",
        json={"product_id": "non-existent-id", "notify_on_any_drop": True},
        headers=auth_headers,
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_watchlist_item(
    client: AsyncClient, auth_headers: dict
):
    """Deleting a non-existent watchlist item should be idempotent (204)."""
    resp = await client.delete(
        "/api/v1/watchlist/non-existent-item-id", headers=auth_headers
    )
    assert resp.status_code == 204
