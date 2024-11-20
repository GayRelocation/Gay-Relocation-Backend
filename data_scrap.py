import json
import uuid

with open("data/data.txt", "r", encoding='utf-8') as file:
    file_content = file.read()

with open("data/data.json", "w") as file:
    # file_content consists of data with title and description
    # title of post start with ###### {title}
    # and below that description of post is written until next title is found
    # we need to extract title and description from file_content

    file_content = file_content.split("######")
    data = []
    for i in range(1, len(file_content)):
        title, description = file_content[i].split("\n", 1)
        id = str(uuid.uuid4())
        data.append({"id": id, "title": title.strip(),
                    "description": description.strip()})

    json.dump(data, file, indent=4)

print("Data is successfully converted to JSON format")
