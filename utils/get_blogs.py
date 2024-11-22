import sqlite3

db_url = "Data/data.db"


def fetch_blogs(document_ids: list[str]) -> dict:
    """
    Fetch blogs from the database using the provided document IDs.
    """
    db = sqlite3.connect(db_url)
    cursor = db.cursor()
    cursor.execute("SELECT * FROM blogs WHERE id IN ({seq})".format(
        seq=','.join(['?'] * len(document_ids))), document_ids)
    blogs = cursor.fetchall()
    cursor.close()
    return [
        {
            "id": blog[0],
            "title": blog[1],
            "description": blog[2],
            "date": blog[3],
            "slug": blog[4]
        } for blog in blogs
    ]
