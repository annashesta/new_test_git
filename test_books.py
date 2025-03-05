import pytest
from sqlalchemy import select
from src.models.books import Book
from fastapi import status
from icecream import ic


# 1. Тест на создание книги
@pytest.mark.asyncio
async def test_create_book(async_client, create_seller):
    seller = create_seller  # Используем фикстуру для создания продавца
    data = {
        "title": "Clean Architecture",
        "author": "Robert Martin",
        "count_pages": 300,
        "year": 2025,
        "seller_id": seller.id,  # Добавляем seller_id
    }
    response = await async_client.post("/api/v1/books/", json=data)

    assert response.status_code == status.HTTP_201_CREATED

    result_data = response.json()
    assert result_data["title"] == "Clean Architecture"
    assert result_data["author"] == "Robert Martin"
    assert result_data["pages"] == 300
    assert result_data["year"] == 2025
    assert result_data["seller_id"] == seller.id


# 2. Тест на проверку актуальности книги (издана не позже 2020 года)
@pytest.mark.asyncio
async def test_create_book_with_old_year(async_client):
    # Данные для создания книги с годом издания раньше 2020
    data = {
        "title": "Old Book",
        "author": "Old Author",
        "count_pages": 300,
        "year": 1999,
        "seller_id": 1,
    }

    # Выполняем запрос на создание книги
    response = await async_client.post("/api/v1/books/", json=data)

    # Проверяем статус ответа
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Проверяем содержимое ответа
    assert "Year is too old!" in response.text


# 3. Тест на получение списка книг
@pytest.mark.asyncio
async def test_get_books(db_session, async_client, create_seller):
    # Создаем продавца через фикстуру
    seller = create_seller

    # Создаем книги, связанные с этим продавцом
    book = Book(
        author="Pushkin",
        title="Eugeny Onegin",
        year=2001,
        pages=104,
        seller_id=seller.id,  # Привязываем книгу к созданному продавцу
    )
    book_2 = Book(
        author="Lermontov",
        title="Mziri",
        year=1997,
        pages=104,
        seller_id=seller.id,  # Привязываем книгу к созданному продавцу
    )

    db_session.add_all([book, book_2])
    await db_session.flush()
    await db_session.commit()  # Завершаем транзакцию

    # Выполняем запрос на получение всех книг
    response = await async_client.get("/api/v1/books/")

    # Проверяем статус ответа
    assert response.status_code == status.HTTP_200_OK

    # Проверяем количество книг
    result_data = response.json()
    assert len(result_data["books"]) == 2

    # Проверяем интерфейс ответа
    assert result_data == {
        "books": [
            {
                "id": book.id,
                "title": "Eugeny Onegin",
                "author": "Pushkin",
                "year": 2001,
                "pages": 104,
                "seller_id": seller.id,  # Используем реальный ID продавца
            },
            {
                "id": book_2.id,
                "title": "Mziri",
                "author": "Lermontov",
                "year": 1997,
                "pages": 104,
                "seller_id": seller.id,  # Используем реальный ID продавца
            },
        ]
    }


# 4. Тест на получение одной книги
@pytest.mark.asyncio
async def test_get_single_book(db_session, async_client, create_seller):
    seller = create_seller  # Используем фикстуру для создания продавца

    # Создаем книгу, связанную с продавцом
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)
    db_session.add(book)
    await db_session.flush()

    response = await async_client.get(f"/api/v1/books/{book.id}")

    assert response.status_code == status.HTTP_200_OK

    # Проверяем интерфейс ответа
    assert response.json() == {
        "id": book.id,
        "title": "Eugeny Onegin",
        "author": "Pushkin",
        "year": 2001,
        "pages": 104,
        "seller_id": seller.id,  # Проверяем seller_id
    }


# 5. Тест на получение несуществующей книги
@pytest.mark.asyncio
async def test_get_no_book(db_session, async_client):
    # Выполняем запрос на получение несуществующей книги
    response = await async_client.get("/api/v1/books/999")

    # Проверяем статус ответа
    assert response.status_code == status.HTTP_404_NOT_FOUND


# 6. Тест на обновление книги
@pytest.mark.asyncio
async def test_update_book(db_session, async_client, create_seller):
    seller = create_seller  # Используем фикстуру для создания продавца

    # Создаем книгу, связанную с продавцом
    book = Book(author="Pushkin", title="Eugeny Onegin", year=2001, pages=104, seller_id=seller.id)
    db_session.add(book)
    await db_session.flush()

    updated_data = {
        "title": "Mziri",
        "author": "Lermontov",
        "pages": 100,
        "year": 2007,
        "id": book.id,
        "seller_id": seller.id,  # Оставляем тот же seller_id
    }

    response = await async_client.put(f"/api/v1/books/{book.id}", json=updated_data)

    assert response.status_code == status.HTTP_200_OK

    # Проверяем, что данные обновились в базе
    updated_book = await db_session.get(Book, book.id)
    assert updated_book.title == "Mziri"
    assert updated_book.author == "Lermontov"
    assert updated_book.pages == 100
    assert updated_book.year == 2007
    assert updated_book.seller_id == seller.id  # Проверяем seller_id


# 7. Тест на обновление несуществующей книги
@pytest.mark.asyncio
async def test_update_no_book(db_session, async_client):
    # Данные для обновления
    updated_data = {
        "id": 1,
        "title": "Updated Title",
        "author": "Updated Author",
        "year": 2023,
        "pages": 400,
        "seller_id": 2,
    }

    # Выполняем запрос на обновление несуществующей книги
    response = await async_client.put("/api/v1/books/999", json=updated_data)

    # Проверяем статус ответа
    assert response.status_code == status.HTTP_404_NOT_FOUND


# 8. Тест на удаление книги
@pytest.mark.asyncio
async def test_delete_book(db_session, async_client, create_seller):
    seller = create_seller  # Используем фикстуру для создания продавца

    # Создаем книгу, связанную с продавцом
    book = Book(author="Lermontov", title="Mtziri", pages=510, year=2024, seller_id=seller.id)
    db_session.add(book)
    await db_session.commit()  # Фиксируем изменения в базе данных

    # Удаляем книгу
    response = await async_client.delete(f"/api/v1/books/{book.id}")
    assert response.status_code == status.HTTP_204_NO_CONTENT

    # Проверяем, что книга удалена из базы
    all_books = await db_session.execute(select(Book))
    books = all_books.scalars().all()
    assert len(books) == 0


# 9. Тест на удаление несуществующей книги
@pytest.mark.asyncio
async def test_delete_nonexistent_book(db_session, async_client):
    # Выполняем запрос на удаление несуществующей книги
    response = await async_client.delete("/api/v1/books/999")

    # Проверяем статус ответа
    assert response.status_code == status.HTTP_404_NOT_FOUND