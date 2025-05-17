import pytest
from fastapi.testclient import TestClient
from neuronpedia_inference_client.models.activation_topk_by_token_post200_response import (
    ActivationTopkByTokenPost200Response,
)
from neuronpedia_inference_client.models.activation_topk_by_token_post_request import (
    ActivationTopkByTokenPostRequest,
)

from tests.conftest import (
    BOS_TOKEN_STR,
    TEST_PROMPT,
    TOPK_BY_TOKEN_ENDPOINT,
    X_SECRET_KEY,
)


def test_activation_topk_by_token_basic(client: TestClient):
    """
    Test basic functionality of the /activation/topk-by-token endpoint with a simple request.
    """
    request = ActivationTopkByTokenPostRequest(
        prompt=TEST_PROMPT,
        model="gpt2-small",
        source="7-res-jb",
        top_k=3,
        ignore_bos=True,
    )

    response = client.post(
        TOPK_BY_TOKEN_ENDPOINT,
        json=request.model_dump(),
        headers={"X-SECRET-KEY": X_SECRET_KEY},
    )

    assert response.status_code == 200

    # Validate the structure with Pydantic model
    data = response.json()
    response_model = ActivationTopkByTokenPost200Response(**data)

    # Ensure we received non-empty results
    assert len(response_model.tokens) > 0, "No tokens returned"
    assert len(response_model.results) > 0, "No results returned"

    # Check that each token has the requested number of top features
    for result in response_model.results:
        assert (
            len(result.top_features) == 3
        ), f"Expected 3 top features, got {len(result.top_features)}"
        # Check that features are sorted by activation value
        activation_values = [
            feature.activation_value for feature in result.top_features
        ]
        assert activation_values == sorted(
            activation_values, reverse=True
        ), "Features not sorted by activation value"


def test_activation_topk_by_token_with_bos(client: TestClient):
    """
    Test the endpoint with ignore_bos=False to verify BOS token handling.
    """
    request = ActivationTopkByTokenPostRequest(
        prompt=TEST_PROMPT,
        model="gpt2-small",
        source="7-res-jb",
        top_k=3,
        ignore_bos=False,
    )

    response = client.post(
        TOPK_BY_TOKEN_ENDPOINT,
        json=request.model_dump(),
        headers={"X-SECRET-KEY": X_SECRET_KEY},
    )

    assert response.status_code == 200
    data = response.json()
    response_model = ActivationTopkByTokenPost200Response(**data)

    # Verify BOS token is included
    assert response_model.tokens[0] == BOS_TOKEN_STR, "BOS token not found at start"
    assert len(response_model.results) == len(
        response_model.tokens
    ), "Results length doesn't match tokens length"


def test_activation_topk_by_token_invalid_source(client: TestClient):
    """
    Test error handling for an invalid source.
    """
    request = ActivationTopkByTokenPostRequest(
        prompt=TEST_PROMPT,
        model="gpt2-small",
        source="invalid-source",
        top_k=3,
        ignore_bos=True,
    )

    with pytest.raises(AssertionError) as excinfo:
        client.post(
            TOPK_BY_TOKEN_ENDPOINT,
            json=request.model_dump(),
            headers={"X-SECRET-KEY": X_SECRET_KEY},
        )

    assert "Found 0 entries when searching for gpt2-small/invalid-source" in str(
        excinfo.value
    )


def test_activation_topk_by_token_long_prompt(client: TestClient):
    """
    Test handling of a prompt that exceeds the token limit.
    """
    # Create a very long prompt that will exceed the token limit
    long_prompt = "This is a test prompt. " * 1000  # Repeat the prompt 1000 times

    request = ActivationTopkByTokenPostRequest(
        prompt=long_prompt,
        model="gpt2-small",
        source="7-res-jb",
        top_k=3,
        ignore_bos=True,
    )

    response = client.post(
        TOPK_BY_TOKEN_ENDPOINT,
        json=request.model_dump(),
        headers={"X-SECRET-KEY": X_SECRET_KEY},
    )

    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "Text too long" in data["error"]
