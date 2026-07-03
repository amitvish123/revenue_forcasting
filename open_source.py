import requests
import json

LOGIN_URL = "https://www.api.mospi.gov.in/api/users/login"
CPI_URL = "https://www.api.mospi.gov.in/api/cpi/getCPIIndex"

USERNAME = "vishwaamit015@gmail.com"
PASSWORD = "Test@12345678"


def login():
    payload = {
        "username": USERNAME,
        "password": PASSWORD
    }

    headers = {
        "Content-Type": "application/json"
    }

    response = requests.post(
        LOGIN_URL,
        json=payload,
        headers=headers,
        verify=False
    )

    response.raise_for_status()
    data = response.json()

    # ✅ Improved token extraction (covers most API formats)
    token = (
        data.get("response")
        or data.get("accessToken")
        or data.get("access_token")
        or data.get("data", {}).get("token")
    )

    if not token:
        raise ValueError(f"Token not found in response: {data}")

    return token


def get_cpi(token, base_year=2010, year="2022", month="1", state_code=None):
    headers = {
        # ✅ Try Bearer first (common standard)
        "Authorization": f"{token}",
        "Content-Type": "application/json"
    }

    params = {
        "base_year": base_year,
        "year": year,
        "month_code": month,
        "limit": 20,
        "page": 1
    }

    # add state only if provided
    if state_code:
        params["state_code"] = state_code

    response = requests.get(
        CPI_URL,
        headers=headers,
        params=params,
        verify=False
    )

    response.raise_for_status()
    return response.json()


def save_to_file(data, filename="cpi_result.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


if __name__ == "__main__":
    try:
        token = login()
        print("Login successful. Token received.")

        # Example call (you can loop later for 2014–2025)
        cpi_data = get_cpi(
            token,
            base_year=2010,
            year="2022",
            month="1",
            state_code="27"   # change as needed
        )

        print("CPI data fetched successfully.")
        save_to_file(cpi_data)
        print("Saved to cpi_result.json")

    except Exception as e:
        print("Error:", str(e))