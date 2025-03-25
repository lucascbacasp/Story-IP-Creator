from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command
import uuid


def create_memory_saver():
    """Create a memory saver for the workflow."""
    return MemorySaver()


def process_user_input(prompt):
    """Process user input for image generation."""
    if not prompt:
        prompt = "an anime style image of a person snowboarding"  # Default if empty
        print(f"Using default prompt: '{prompt}'")

    return {"messages": [{"role": "user", "content": f"Generate {prompt}"}]}


def create_config():
    """Create a configuration for the workflow."""
    thread_id = str(uuid.uuid4())
    return {"configurable": {"thread_id": thread_id}}


async def handle_interrupt(event, process_events_func):
    """Handle interrupts from the workflow."""
    if "__interrupt__" in event:
        interrupt_data = event["__interrupt__"][0].value

        # Check which type of interrupt we're dealing with
        if "image_url" in interrupt_data:
            # This is the image review interrupt
            # Display the image URL once so the user can see what was generated
            print(f"\nGenerated image: {interrupt_data['image_url']}\n")

            user_input = input("Do you like this image? (yes/no + feedback): ")

            if user_input.lower().startswith("yes"):
                # Continue to IPFS upload
                print("Uploading image to IPFS...")
                await process_events_func(Command(resume={"action": "continue"}))
            else:
                # Get feedback after "no"
                feedback = (
                    user_input[4:]
                    if len(user_input) > 4
                    else "Please generate a different image"
                )
                print("Generating a new image...")
                await process_events_func(
                    Command(resume={"action": "feedback", "data": feedback})
                )

        elif "fields" in interrupt_data:
            # Check if this is the terms negotiation interrupt
            if "commercial_rev_share" in [
                field["name"] for field in interrupt_data.get("fields", [])
            ]:
                # This is the initial terms negotiation interrupt
                print("\n" + interrupt_data.get("explanation", ""))

                # Get commercial revenue share
                while True:
                    try:
                        rev_share = int(
                            input(
                                "Enter Commercial Revenue Share (0-100%, default: 15%): "
                            )
                            or "15"
                        )
                        if 0 <= rev_share <= 100:
                            break
                        print("Please enter a value between 0 and 100.")
                    except ValueError:
                        print("Please enter a valid number.")

                # Get derivatives allowed
                while True:
                    deriv_input = (
                        input(
                            "Allow Derivative Works? (yes/no, default: yes): "
                        ).lower()
                        or "yes"
                    )
                    if deriv_input in ["yes", "no", "y", "n"]:
                        derivatives_allowed = deriv_input.startswith("y")
                        break
                    print("Please enter yes or no.")

                # Resume with the user's choices
                await process_events_func(
                    Command(
                        resume={
                            "commercial_rev_share": rev_share,
                            "derivatives_allowed": derivatives_allowed,
                        }
                    )
                )

            # Check if this is the feedback on terms interrupt
            elif "adjust_terms" in [
                field["name"] for field in interrupt_data.get("fields", [])
            ]:
                # This is the feedback on terms interrupt
                print("\n" + interrupt_data.get("explanation", ""))

                # Ask if user wants to adjust terms
                while True:
                    adjust_input = input(
                        "Would you like to adjust your terms based on this feedback? (yes/no, default: yes): "
                    ).lower()
                    if adjust_input in [
                        "yes",
                        "no",
                        "y",
                        "n",
                        "",
                    ]:  # Empty string for default
                        adjust_terms = not (
                            adjust_input.startswith("n")
                        )  # Default to yes
                        break
                    print("Please enter yes or no.")

                # Resume with the user's choice
                await process_events_func(
                    Command(resume={"adjust_terms": adjust_terms})
                )

            # Check if this is the term adjustment interrupt
            elif (
                len(interrupt_data.get("fields", [])) == 2
                and "commercial_rev_share"
                in [field["name"] for field in interrupt_data.get("fields", [])]
                and "derivatives_allowed"
                in [field["name"] for field in interrupt_data.get("fields", [])]
            ):
                # This is the term adjustment interrupt
                print("\n" + interrupt_data.get("explanation", ""))

                # Get commercial revenue share
                while True:
                    try:
                        rev_share = int(
                            input(
                                f"Enter Commercial Revenue Share (0-100%, default: {interrupt_data['fields'][0].get('default', 15)}%): "
                            )
                            or str(interrupt_data["fields"][0].get("default", 15))
                        )
                        if 0 <= rev_share <= 100:
                            break
                        print("Please enter a value between 0 and 100.")
                    except ValueError:
                        print("Please enter a valid number.")

                # Get derivatives allowed
                while True:
                    default_deriv = (
                        "yes"
                        if interrupt_data["fields"][1].get("default", True)
                        else "no"
                    )
                    deriv_input = (
                        input(
                            f"Allow Derivative Works? (yes/no, default: {default_deriv}): "
                        ).lower()
                        or default_deriv
                    )
                    if deriv_input in ["yes", "no", "y", "n"]:
                        derivatives_allowed = deriv_input.startswith("y")
                        break
                    print("Please enter yes or no.")

                # Resume with the user's choices
                await process_events_func(
                    Command(
                        resume={
                            "commercial_rev_share": rev_share,
                            "derivatives_allowed": derivatives_allowed,
                        }
                    )
                )

            else:
                # Generic fields handler
                print("Please provide the requested information:")
                responses = {}

                for field in interrupt_data.get("fields", []):
                    field_name = field.get("name", "")
                    field_type = field.get("type", "text")
                    field_default = field.get("default", "")
                    field_label = field.get("label", field_name)

                    if field_type == "boolean":
                        while True:
                            value_input = input(
                                f"{field_label}? (yes/no, default: {'yes' if field_default else 'no'}): "
                            ).lower() or ("yes" if field_default else "no")
                            if value_input in ["yes", "no", "y", "n"]:
                                responses[field_name] = value_input.startswith("y")
                                break
                            print("Please enter yes or no.")

                    elif field_type == "slider":
                        min_val = field.get("min", 0)
                        max_val = field.get("max", 100)
                        while True:
                            try:
                                value_input = input(
                                    f"{field_label} ({min_val}-{max_val}, default: {field_default}): "
                                ) or str(field_default)
                                value = int(value_input)
                                if min_val <= value <= max_val:
                                    responses[field_name] = value
                                    break
                                print(
                                    f"Please enter a value between {min_val} and {max_val}."
                                )
                            except ValueError:
                                print("Please enter a valid number.")

                    else:  # text or other types
                        value_input = input(
                            f"{field_label} (default: {field_default}): "
                        ) or str(field_default)
                        responses[field_name] = value_input

                # Resume with all responses
                await process_events_func(Command(resume=responses))

        else:
            # Generic interrupt handler for any other interrupts
            user_input = input("Enter your response: ")
            await process_events_func(Command(resume={"data": user_input}))
