import httpx
import asyncio
from typing import Union, Any


async def get_response(url: str) -> Union[dict, Any]:
    """Получение ответа от стороннего API."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to get the response'}


async def get_sustenance_by_position(
        latitude: float,
        longitude: float,
        around: int) -> Union[dict, Any]:
    """Запрос мест по координатом и радиусу."""
    url = ('https://overpass-api.de/api/interpreter?data=[out:json];'
           '(node['
           'amenity~'
           '"bar|'
           'biergarten|'
           'cafe|'
           'fast_food|'
           'food_court|'
           'ice_cream|'
           'pub|'
           'restaurant"'
           ']'
           f'(around:{around},{latitude},{longitude}););out;')

    return await get_response(url=url)


async def get_places_by_id(place_ids: list[str]) -> Union[dict, Any]:
    place_ids_str = ', '.join(place_ids)
    """Запрос списка мест по списку id."""
    url = ('https://overpass-api.de/api/interpreter?data=[out:json];'
           '(node(id:'
           f'{place_ids_str}'
           '););out;')

    return await get_response(url=url)


async def get_region_boundingbox(region_name: str) -> Union[dict, Any]:
    """Запрос границ координат локации по названию."""

    url = ('https://nominatim.openstreetmap.org/'
           f'search?format=json&q={region_name}')
    response = await get_response(url=url)
    return response[0]['boundingbox']


async def get_search_by_name(
        region_name: str,
        place_name: str) -> Union[dict, Any]:
    """Запрос места по названию."""
    boundingbox = await get_region_boundingbox(region_name)
    south, north, west, east = boundingbox
    SEARCH_LIMIT = 10
    url = ('https://overpass-api.de/api/interpreter?data=[out:json];'
           'node[amenity~"'
           'bar|biergarten|cafe|fast_food|food_court|ice_cream|pub|restaurant'
           '"]'
           f'["name"="{place_name}"]'
           f'({south},{west},{north},{east})'
           f';out {SEARCH_LIMIT};')

    return await get_response(url=url)


async def get_place_by_id(place_id: str) -> Union[dict, Any]:
    """Запрос места по id места."""
    url = ('https://overpass-api.de/api/interpreter?data=[out:json];'
           f'(node(id:{place_id}););out;')

    return await get_response(url=url)


if __name__ == '__main__':
    result = asyncio.run(
        get_sustenance_by_position(36.8837384, 30.7093815, 200))
    print(result)
