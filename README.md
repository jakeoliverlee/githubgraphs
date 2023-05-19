![image](https://github.com/jakeoliverlee/githubgraphs/assets/22305022/d013b870-e37b-45bc-bb09-f0a069057e98)
## Getting started


This API provides a function for getting a commit graph for a particular GitHub repository.

## Base URL

All API requests should be made to: `https://jakeoliverlee-githubgraphs.nw.r.appspot.com`

## Endpoints

### `GET /v1/commit-graph`

This endpoint generates and returns an SVG graph of commit counts for your specified GitHub repository.


#### Request parameters

| Parameter | Description | Type | Default |
| --- | --- | --- | --- |
| username | The username of the repo owner | str | None |
| repo | The name of the repo | str | None |
| period | The period to analyze the commits. Possible values are "month", "year", "all" | str | "month" |
| theme | The theme for the graph. Possible values are "dark", "light", "sunset", "forest", "ocean", "sakura", "monochrome", "rainbow" | str | dark |

#### Responses

- 200: Returns an SVG graph as a file with `Content-Type: image/svg+xml`.
- 400: Bad request - when the request parameters are missing or incorrect. The response will include a message describing the error.
- 404: Not found - when the requested repository is not found. The response will include a message describing the error.

#### Example usage

```GET /v1/commit-graph?username=testUser&repo=testRepo&period=week&theme=light```

#### Example error response

```json
{
    "message": "invalid period, please choose from the available periods : ['month', 'year', 'all']",
    "status_code": 400
}
```

## Some examples:

| Badge                                                                                                                  | URL                                                                         | Theme                                                                                          |
| ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| <img width='' src="/assets/dark.svg"/> | `https://jakeoliverlee-githubgraphs.nw.r.appspot.com/v1/commit-graph?username=jakeoliverlee&repo=jakeoliverlee.com` | `Default (dark)` |
| <img width='' src="/assets/light.svg" /> | `https://jakeoliverlee-githubgraphs.nw.r.appspot.com/v1/commit-graph?username=jakeoliverlee&repo=jakeoliverlee.com&theme=light` | `light` |
| <img width='' src="/assets/sunset.svg" /> | `https://jakeoliverlee-githubgraphs.nw.r.appspot.com/v1/commit-graph?username=jakeoliverlee&repo=jakeoliverlee.com&theme=sunset` | `sunset` |
| <img width='' src="/assets/forest.svg" /> | `https://jakeoliverlee-githubgraphs.nw.r.appspot.com/v1/commit-graph?username=jakeoliverlee&repo=jakeoliverlee.com&theme=forest` | `forest` |
| <img width='' src="/assets/ocean.svg" /> | `https://jakeoliverlee-githubgraphs.nw.r.appspot.com/v1/commit-graph?username=jakeoliverlee&repo=jakeoliverlee.com&theme=ocean` | `ocean` |
| <img width='' src="/assets/sakura.svg" /> | `https://jakeoliverlee-githubgraphs.nw.r.appspot.com/v1/commit-graph?username=jakeoliverlee&repo=jakeoliverlee.com&theme=sakura` | `sakura` |
| <img width='' src="/assets/monochrome.svg" /> | `https://jakeoliverlee-githubgraphs.nw.r.appspot.com/v1/commit-graph?username=jakeoliverlee&repo=jakeoliverlee.com&theme=monochrome` | `monochrome` |
| <img width='' src="/assets/rainbow.svg" /> | `https://jakeoliverlee-githubgraphs.nw.r.appspot.com/v1/commit-graph?username=jakeoliverlee&repo=jakeoliverlee.com&theme=rainbow` | `rainbow` |



