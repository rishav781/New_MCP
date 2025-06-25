from config import Config, logger
import httpx
import json
from utils import encode_auth, parse_response

class AdbMixin:
    async def execute_adb_command(self, rid: str, adb_command: str):
        await self.check_token_validity()
        if not adb_command.strip():
            raise ValueError("ADB command cannot be empty")
        original_command = adb_command.strip().strip('"').strip("'")
        # Ensure 'adb ' prefix is present for backend compatibility
        if not original_command.lower().startswith('adb '):
            send_command = f'adb {original_command}'
            logger.info(f"Added 'adb' prefix: sending '{send_command}' to backend.")
        else:
            send_command = original_command
        logger.info(f"Executing ADB command on RID {rid}: {send_command}")
        url = f"{self.base_url}/execute_adb"
        payload = {
            "token": self.auth_token,
            "rid": rid,
            "adbCommand": send_command
        }
        headers = {"Content-Type": "application/json"}
        timeout_config = httpx.Timeout(connect=30.0, read=120.0, write=30.0, pool=30.0)
        async with httpx.AsyncClient(timeout=timeout_config) as client:
            logger.debug(f"Sending ADB request to: {url}")
            logger.debug(f"Payload: {json.dumps(payload, indent=2)}")
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            raw_data = response.json()
            logger.info(f"Raw ADB response: {json.dumps(raw_data, indent=2)}")
            if isinstance(raw_data, dict):
                result = raw_data.get("result", raw_data)
                status_code = result.get("code", 0)
                message = result.get("msg", "")
                output_content = None
                output_source = None
                for field_name in ["adbreply", "output", "reply", "response", "data", "result"]:
                    if field_name in result and result[field_name] is not None:
                        output_content = result[field_name]
                        output_source = field_name
                        break
                if output_content is not None:
                    formatted_output = str(output_content)
                    if "\n" in formatted_output:
                        formatted_output = formatted_output.replace("\n", "\n")
                    formatted_output = formatted_output.strip()
                    if not formatted_output:
                        formatted_output = "[Command executed successfully but returned empty output]"
                else:
                    formatted_output = "[No output returned from device]"
                    logger.warning(f"No output found in response fields. Available keys: {list(result.keys())}")
                is_success = status_code == 200 and "Invalid Command" not in formatted_output
                if is_success:
                    logger.info(f"ADB command successful. Output source: {output_source}, Length: {len(formatted_output)}")
                    return {
                        "success": True,
                        "output": formatted_output,
                        "command": send_command,
                        "rid": rid,
                        "status_code": status_code,
                        "message": message,
                        "output_source": output_source
                    }
                else:
                    error_msg = f"ADB command failed: {formatted_output}"
                    logger.error(error_msg)
                    return {
                        "success": False,
                        "error": error_msg,
                        "command": send_command,
                        "rid": rid,
                        "status_code": status_code,
                        "raw_response": raw_data
                    }
            else:
                logger.error(f"Unexpected response format: {type(raw_data)}")
                return {
                    "success": False,
                    "error": f"Unexpected response format: {type(raw_data)}",
                    "command": send_command,
                    "rid": rid
                }