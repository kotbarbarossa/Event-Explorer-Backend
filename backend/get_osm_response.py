import httpx
import asyncio


async def get_sustenance_by_position(
        latitude: int,
        longitude: float,
        around: float):
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

    async with httpx.AsyncClient() as client:
        response = await client.get(url)

    if response.status_code == 200:
        return response.json()
    else:
        return {'error': 'Failed to get the response'}


if __name__ == '__main__':
    result = asyncio.run(
        get_sustenance_by_position(36.8837384, 30.7093815, 200))
    print(result)