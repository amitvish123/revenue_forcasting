import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

LOGIN_URL = "https://www.api.mospi.gov.in/api/users/login"
CPI_URL = "https://www.api.mospi.gov.in/api/cpi/getCPIIndex?base_year=2012&state_code=23&year=2026,2025,2024,2023,2022,2021,2020,2019,2018"

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

    response = requests.post(LOGIN_URL, json=payload, headers=headers, verify=False)
    response.raise_for_status()

    data = response.json()

    # Try common token field names (API-dependent)
    token = (
        data.get("response")
        or data.get("accessToken")
        or data.get("access_token")
        or data.get("data", {}).get("token")
    )

    if not token:
        raise ValueError(f"Token not found in response: {data}")

    return token


# def get_cpi(token):
#     headers = {
#         "Authorization": f"{token}",  # sometimes APIs require "Bearer {token}"
#         "Content-Type": "application/json"
#     }

#     response = requests.get(CPI_URL, headers=headers, verify=False)
#     response.raise_for_status()

#     return response.json()


# def save_to_file(data, filename="cpi_result.json"):
#     with open(filename, "w", encoding="utf-8") as f:
#         json.dump(data, f, indent=4, ensure_ascii=False)

def fetch_page(page, headers):
    response = requests.get(
        CPI_URL,
        headers=headers,
        params={"page": page},
        verify=False,
        timeout=30
    )
    response.raise_for_status()
    return response.json()["data"]

def download_all(token):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    # First page to get metadata
    first = requests.get(
        CPI_URL,
        headers=headers,
        params={"page": 1},
        verify=False
    ).json()

    total_pages = first["meta_data"]["totalPages"]

    all_data = first["data"]

    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = {
            executor.submit(fetch_page, page, headers): page
            for page in range(2, total_pages + 1)
        }

        for future in as_completed(futures):
            page = futures[future]

            try:
                all_data.extend(future.result())

                if page % 100 == 0:
                    print(f"Completed page {page}")
            except Exception as e:
                print(f"Page {page} failed: {e}")

    return all_data

def get_all_cpi(token):
    headers = {
        "Authorization": token,
        "Content-Type": "application/json"
    }

    all_records = []

    with requests.Session() as session:
        session.headers.update(headers)

        page = 1

        while True:
            response = session.get(
                CPI_URL,
                params={"page": page, "recordPerPage" : 1000},
                verify=False
            )

            response.raise_for_status()
            result = response.json()

            all_records.extend(result.get("data", []))

            meta = result["meta_data"]
            total_pages = meta["totalPages"]

            print(f"Page {page}/{total_pages}")

            if page >= total_pages:
                break

            page += 1

    return all_records

def save_to_file(data, filename="cpi_result.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=4,
            ensure_ascii=False
        )

if __name__ == "__main__":
    try:
        token = login()
        print("Login successful. Token received.")

        cpi_data = download_all(token)
        print("CPI data fetched successfully.")

        save_to_file(cpi_data)
        print("Saved to cpi_result.json")
        # headers = {
        #     "Authorization": token,
        #     "Content-Type": "application/json"
        # }
        
        # response = requests.get(
        #     CPI_URL,
        #     headers=headers,
        #     params={
        #         "page": 1,
        #         "recordPerPage": 100
        #     },
        #     verify=False
        # )

        # data = response.json()

        # print(data["meta_data"])
        # print(len(data["data"]))


    except Exception as e:
        print("Error:", str(e))