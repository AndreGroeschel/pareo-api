import requests  # noqa: D100


def test_stream() -> None:  # noqa: D103
    url = "http://127.0.0.1:8000/api/v1/investors/match"

    # Your request payload
    payload = {"prompt": "Seed stage AI investors in Europe, Proptech", "threshold": 0.7, "max_entries": 10}  # type: ignore

    # Make sure to set stream=True in the request
    with requests.post(url, json=payload, stream=True, timeout=30) as response:  # type: ignore
        if response.status_code == 200:
            for chunk in response.iter_lines():
                if chunk:
                    # Decode the chunk if it's bytes
                    decoded_chunk = chunk.decode("utf-8")
                    print(f"Received chunk: {decoded_chunk}")
        else:
            print(f"Error: {response.status_code}")


if __name__ == "__main__":
    test_stream()
