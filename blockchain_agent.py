import requests
from dotenv import load_dotenv
import os

# Carga las variables de entorno desde el archivo .env
load_dotenv(dotenv_path="/Users/lucascapdevila/LANGGRAPH-MCP-AGENT/.env")

# URL base del StoryScan MCP Server
STORYSCAN_API_URL = "http://127.0.0.1:8000"

def query_blockchain_data():
    """Permite al usuario consultar datos de blockchain usando StoryScan MCP Server."""
    while True:
        print("\n=== StoryScan Blockchain Query Agent ===")
        print("Opciones disponibles:")
        print("1. Consultar saldo de una dirección (check_balance)")
        print("2. Obtener transacciones recientes de una dirección (get_transactions)")
        print("3. Obtener estadísticas de la blockchain (get_stats)")
        print("4. Obtener resumen de una dirección (get_address_overview)")
        print("5. Obtener tokens ERC-20 de una dirección (get_token_holdings)")
        print("6. Obtener NFTs de una dirección (get_nft_holdings)")
        print("7. Interpretar una transacción (interpret_transaction)")
        print("8. Salir")

        option = input("\nSelecciona una opción (1-8): ")

        if option == "1":
            # Consultar saldo de una dirección
            address = input("Ingresa la dirección de blockchain: ")
            response = requests.post(f"{STORYSCAN_API_URL}/check_balance", json={"address": address})
            if response.status_code == 200:
                data = response.json()
                print(f"Saldo de la dirección {address}: {data.get('balance')}")
            else:
                print(f"Error al consultar saldo: {response.json()}")

        elif option == "2":
            # Obtener transacciones recientes
            address = input("Ingresa la dirección de blockchain: ")
            response = requests.post(f"{STORYSCAN_API_URL}/get_transactions", json={"address": address})
            if response.status_code == 200:
                transactions = response.json().get("transactions", [])
                if transactions:
                    print(f"Transacciones recientes de {address}:")
                    for tx in transactions:
                        print(f"- Hash: {tx.get('hash')}, Monto: {tx.get('amount')}, Fecha: {tx.get('date')}")
                else:
                    print("No se encontraron transacciones recientes.")
            else:
                print(f"Error al obtener transacciones: {response.json()}")

        elif option == "3":
            # Obtener estadísticas de la blockchain
            response = requests.post(f"{STORYSCAN_API_URL}/get_stats")
            if response.status_code == 200:
                stats = response.json()
                print("Estadísticas de la blockchain:")
                for key, value in stats.items():
                    print(f"- {key}: {value}")
            else:
                print(f"Error al obtener estadísticas: {response.json()}")

        elif option == "4":
            # Obtener resumen de una dirección
            address = input("Ingresa la dirección de blockchain: ")
            response = requests.post(f"{STORYSCAN_API_URL}/get_address_overview", json={"address": address})
            if response.status_code == 200:
                overview = response.json()
                print(f"Resumen de la dirección {address}:")
                for key, value in overview.items():
                    print(f"- {key}: {value}")
            else:
                print(f"Error al obtener resumen: {response.json()}")

        elif option == "5":
            # Obtener tokens ERC-20
            address = input("Ingresa la dirección de blockchain: ")
            response = requests.post(f"{STORYSCAN_API_URL}/get_token_holdings", json={"address": address})
            if response.status_code == 200:
                tokens = response.json().get("tokens", [])
                if tokens:
                    print(f"Tokens ERC-20 de {address}:")
                    for token in tokens:
                        print(f"- Token: {token.get('name')}, Saldo: {token.get('balance')}")
                else:
                    print("No se encontraron tokens ERC-20.")
            else:
                print(f"Error al obtener tokens: {response.json()}")

        elif option == "6":
            # Obtener NFTs
            address = input("Ingresa la dirección de blockchain: ")
            response = requests.post(f"{STORYSCAN_API_URL}/get_nft_holdings", json={"address": address})
            if response.status_code == 200:
                nfts = response.json().get("nfts", [])
                if nfts:
                    print(f"NFTs de {address}:")
                    for nft in nfts:
                        print(f"- NFT: {nft.get('name')}, ID: {nft.get('id')}")
                else:
                    print("No se encontraron NFTs.")
            else:
                print(f"Error al obtener NFTs: {response.json()}")

        elif option == "7":
            # Interpretar una transacción
            tx_hash = input("Ingresa el hash de la transacción: ")
            response = requests.post(f"{STORYSCAN_API_URL}/interpret_transaction", json={"tx_hash": tx_hash})
            if response.status_code == 200:
                interpretation = response.json().get("interpretation")
                print(f"Interpretación de la transacción {tx_hash}:")
                print(interpretation)
            else:
                print(f"Error al interpretar transacción: {response.json()}")

        elif option == "8":
            print("Saliendo del agente. ¡Gracias por usar StoryScan Blockchain Query Agent!")
            break
        else:
            print("Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    query_blockchain_data()
