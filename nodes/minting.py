from langchain_core.messages import AIMessage, ToolMessage
from langchain_core.runnables import RunnableLambda
import uuid
import re
import json
import traceback


class MintRegisterIP:
    """Node for minting and registering the IP on the blockchain."""

    def __init__(self, mint_register_ip_tool):
        self.mint_register_ip_tool = mint_register_ip_tool

    async def ainvoke(self, state, config=None):
        print("Minting and registering IP...")

        # Get the terms data from the previous message
        terms_data = None
        for message in reversed(state["messages"]):
            if (
                isinstance(message, AIMessage)
                and hasattr(message, "additional_kwargs")
                and "terms_data" in message.additional_kwargs
            ):
                terms_data = message.additional_kwargs["terms_data"]
                break

        if not terms_data:
            return {
                "messages": [
                    AIMessage(
                        content="Failed to extract terms data from previous steps."
                    )
                ]
            }

        try:
            # Extract the parameters
            commercial_rev_share = terms_data["commercial_rev_share"]
            derivatives_allowed = terms_data["derivatives_allowed"]
            registration_metadata = terms_data["registration_metadata"]

            # Fix the metadata format - ensure hashes have 0x prefix
            fixed_metadata = {}
            if registration_metadata:
                fixed_metadata = {
                    "ip_metadata_uri": registration_metadata.get("ip_metadata_uri", ""),
                    "ip_metadata_hash": registration_metadata.get(
                        "ip_metadata_hash", ""
                    ),
                    "nft_metadata_uri": registration_metadata.get(
                        "nft_metadata_uri", ""
                    ),
                    "nft_metadata_hash": registration_metadata.get(
                        "nft_metadata_hash", ""
                    ),
                }

                # Add 0x prefix to hashes if missing
                if "ip_metadata_hash" in fixed_metadata and not fixed_metadata[
                    "ip_metadata_hash"
                ].startswith("0x"):
                    fixed_metadata["ip_metadata_hash"] = (
                        "0x" + fixed_metadata["ip_metadata_hash"]
                    )

                if "nft_metadata_hash" in fixed_metadata and not fixed_metadata[
                    "nft_metadata_hash"
                ].startswith("0x"):
                    fixed_metadata["nft_metadata_hash"] = (
                        "0x" + fixed_metadata["nft_metadata_hash"]
                    )

            # Convert parameters to strings as expected by the tool
            tool_args = {
                "commercial_rev_share": str(commercial_rev_share),
                "derivatives_allowed": str(derivatives_allowed).lower(),
                "registration_metadata": fixed_metadata,
            }

            # Call the mint_and_register_ip_with_terms tool
            result = await self.mint_register_ip_tool.ainvoke(tool_args)

            # Check if there was an error related to derivatives
            if (
                "Cannot add derivative attribution when derivative use is disabled"
                in result
            ):
                # Retry with derivatives allowed
                tool_args["derivatives_allowed"] = "true"
                result = await self.mint_register_ip_tool.ainvoke(tool_args)

            ip_id = None
            tx_hash = None
            license_terms_ids = []

            # Extract IP ID
            ip_id_match = re.search(r"IP ID: (0x[a-fA-F0-9]+)", result)
            if ip_id_match:
                ip_id = ip_id_match.group(1)
                # Print the IP link in the requested format
                print(f"\n@https://aeneid.explorer.story.foundation/ipa/{ip_id}")

            # Extract Transaction Hash
            tx_hash_match = re.search(r"Transaction Hash: ([a-fA-F0-9]+)", result)
            if tx_hash_match:
                tx_hash = tx_hash_match.group(1)
                # Print the transaction link in the requested format
                print(f"@https://aeneid.storyscan.xyz/tx/0x{tx_hash}")

            # Extract License Terms IDs
            license_terms_match = re.search(r"License Terms IDs: \[(.*?)\]", result)
            if license_terms_match:
                terms_str = license_terms_match.group(1)
                # Parse the comma-separated list
                if terms_str:
                    license_terms_ids = [
                        int(term.strip())
                        for term in terms_str.split(",")
                        if term.strip().isdigit()
                    ]

            # If we still don't have an IP ID, the minting failed
            if not ip_id:
                # Try one more time with more reasonable defaults and fixed metadata format
                tool_args = {
                    "commercial_rev_share": "15",
                    "derivatives_allowed": "true",
                    "registration_metadata": fixed_metadata,
                }

                print(f"\n--- Final Retry Arguments ---")
                print(json.dumps(tool_args, indent=2))
                print("----------------------------\n")

                result = await self.mint_register_ip_tool.ainvoke(tool_args)

                # Extract IP ID again
                ip_id_match = re.search(r"IP ID: (0x[a-fA-F0-9]+)", result)
                if ip_id_match:
                    ip_id = ip_id_match.group(1)
                    # Print the IP link in the requested format
                    print(f"\n@https://aeneid.explorer.story.foundation/ipa/{ip_id}")

                # Extract Transaction Hash again
                tx_hash_match = re.search(r"Transaction Hash: ([a-fA-F0-9]+)", result)
                if tx_hash_match:
                    tx_hash = tx_hash_match.group(1)
                    # Print the transaction link in the requested format
                    print(f"@https://aeneid.storyscan.xyz/tx/0x{tx_hash}")

                # Extract License Terms IDs again
                license_terms_match = re.search(r"License Terms IDs: \[(.*?)\]", result)
                if license_terms_match:
                    terms_str = license_terms_match.group(1)
                    if terms_str:
                        license_terms_ids = [
                            int(term.strip())
                            for term in terms_str.split(",")
                            if term.strip().isdigit()
                        ]

            return {
                "messages": [
                    ToolMessage(
                        content=result,
                        name="mint_and_register_ip_with_terms",
                        tool_call_id=str(uuid.uuid4()),
                        additional_kwargs={
                            "minting_data": {
                                "ip_id": ip_id,
                                "license_terms_ids": license_terms_ids,
                                "tx_hash": tx_hash,
                            }
                        },
                    )
                ]
            }

        except Exception as e:
            print(f"\n--- Exception in MintRegisterIP ---")
            print(traceback.format_exc())
            print("----------------------------\n")

            return {
                "messages": [
                    ToolMessage(
                        content=f"Error minting and registering IP: {str(e)}",
                        name="mint_and_register_ip_with_terms",
                        tool_call_id=str(uuid.uuid4()),
                    )
                ]
            }


class MintLicenseTokens:
    """Node for minting license tokens for the IP."""

    def __init__(self, mint_license_tokens_tool):
        self.mint_license_tokens_tool = mint_license_tokens_tool

    async def ainvoke(self, state, config=None):
        print("Minting license tokens...")

        # Get the minting data from the previous message
        minting_data = None
        for message in reversed(state["messages"]):
            if (
                isinstance(message, ToolMessage)
                and hasattr(message, "additional_kwargs")
                and "minting_data" in message.additional_kwargs
            ):
                minting_data = message.additional_kwargs["minting_data"]
                break

        if (
            not minting_data
            or not minting_data.get("ip_id")
            or not minting_data.get("license_terms_ids")
        ):
            return {
                "messages": [
                    AIMessage(
                        content="Failed to extract IP ID or license terms IDs from previous steps."
                    )
                ]
            }

        try:
            # Extract the parameters
            ip_id = minting_data["ip_id"]
            license_terms_id = (
                minting_data["license_terms_ids"][0]
                if minting_data["license_terms_ids"]
                else None
            )

            if not license_terms_id:
                return {
                    "messages": [
                        AIMessage(
                            content="No license terms ID available for minting license tokens."
                        )
                    ]
                }

            # Call the mint_license_tokens tool
            result = await self.mint_license_tokens_tool.ainvoke(
                {"licensor_ip_id": ip_id, "license_terms_id": license_terms_id}
            )

            # Print the mint license tokens result
            print(
                f"\n--- Mint License Tokens Tool Result ---\n{result}\n----------------------------"
            )

            # Extract Transaction Hash for license token
            tx_hash_match = re.search(r"Transaction Hash: ([a-fA-F0-9]+)", result)
            if tx_hash_match:
                tx_hash = tx_hash_match.group(1)
                # Print the transaction link in the requested format
                print(f"@https://aeneid.storyscan.xyz/tx/0x{tx_hash}")

            return {
                "messages": [
                    ToolMessage(
                        content=result,
                        name="mint_license_tokens",
                        tool_call_id=str(uuid.uuid4()),
                    )
                ]
            }

        except Exception as e:
            return {
                "messages": [
                    ToolMessage(
                        content=f"Error minting license tokens: {str(e)}",
                        name="mint_license_tokens",
                        tool_call_id=str(uuid.uuid4()),
                    )
                ]
            }


def create_mint_register_ip_node(mint_register_ip_tool):
    """Create a callable node for minting and registering IP."""
    return RunnableLambda(MintRegisterIP(mint_register_ip_tool).ainvoke)


def create_mint_license_tokens_node(mint_license_tokens_tool):
    """Create a callable node for minting license tokens."""
    return RunnableLambda(MintLicenseTokens(mint_license_tokens_tool).ainvoke)
