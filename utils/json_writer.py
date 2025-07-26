import orjson

def write_json(data, output_path):
    with open(output_path, "wb") as f:
        f.write(orjson.dumps(data, option=orjson.OPT_INDENT_2))
