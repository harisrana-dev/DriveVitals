from httpx import AsyncClient


class TestRoutes:

    async def test_list_routes(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/routes")

        assert response.status_code == 200
        payload = response.json()
        assert payload["count"] == 3
        assert len(payload["data"]) == 3

    async def test_list_routes_pagination(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/routes", params={"limit": 2})

        assert response.status_code == 200
        payload = response.json()
        assert len(payload["data"]) == 2
        assert payload["count"] == 3

    async def test_get_route(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/routes/r-1")

        assert response.status_code == 200
        route = response.json()["data"]
        assert route["route_id"] == "r-1"
        assert route["origin"] == "Warehouse"
        assert route["destination"] == "Customer A"

    async def test_get_route_not_found(self, client: AsyncClient) -> None:
        response = await client.get("/api/v1/routes/does-not-exist")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
