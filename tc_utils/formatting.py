import json
import re
from enum import Enum
from typing import Dict, Any, Optional, Tuple, List

brace_with_or_without_comma_re = re.compile(r'},?')
bracket_with_or_without_comma_re = re.compile(r'],?')

station_re = (re.compile(r'"(stations|pathSuggestion)": \['), re.compile(r']'))
needed_capacity_re = (re.compile(r'"neededCapacity": \['), bracket_with_or_without_comma_re)

acc_res: List[Tuple[re.Pattern, re.Pattern]] = [station_re]


def format_json(data: Dict[str, Any]) -> str:
    json_string = json.dumps(data, ensure_ascii=False, indent='\t')
    lines = []
    line_acc = []
    end_re: Optional[re.Pattern] = None
    accumulating: bool = False
    # Helper to identify multiple lines
    state: int = 0
    for line in json_string.split('\n'):
        #lines.append(line)
        #continue
        if not end_re:
            # Look if the line matches the accumulating REs
            if station_re[0].match(line.strip()):
                # We have stations. We need to remove the last opening brace and add it to the acc
                #if lines[-1].strip() == '{':
                #    print("Add previous {")
                #    line_acc.append(lines.pop(-1).rstrip())
                #    line_acc.append(line.strip())
                #else:
                line_acc.append(line)
                end_re = station_re[1]
            elif needed_capacity_re[0].match(line.strip()):
                # We won't add it to the accumulator yet, but we will in the next line
                state = 1
                lines.append(line)
            elif state == 1:
                # We are in a neededCapacity block.
                if line.strip() == '{':
                    # Start neededCapacity entry
                    state = 4
                    end_re = brace_with_or_without_comma_re
                    line_acc.append(line)
                if bracket_with_or_without_comma_re.match(line.strip()):
                    # Closing neededCapacity, return to normal
                    lines.append(line)
                    state = 0
            else:
                state = 0
                lines.append(line)
        else:
            line_acc.append(line.strip())
            if end_re.match(line.strip()):
                # Finish the accumulation
                lines.append(' '.join(line_acc))
                line_acc.clear()
                end_re = None
                if state == 4:
                    state = 1
                else:
                    state = 0
    return '\n'.join(lines)
