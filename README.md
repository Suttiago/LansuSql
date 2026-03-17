# lansuSql 🚀

A robust, fully-typed Generic Repository library for Python, bridging the gap between **SQLAlchemy** and **Pydantic**. 

Say goodbye to repetitive database queries. `lansuSql` provides an elegant, Django-style ORM experience for your FastAPI/SQLAlchemy projects, complete with dynamic filtering and native DTO support.

## ✨ Features

- **CRUD Out-of-the-Box:** Standard methods for creating, reading, updating, and deleting records without writing repetitive SQLAlchemy statements.
- **Django-style Dynamic Filters:** Query your database intuitively using operators like `__gt`, `__lt`, `__gte`, `__in`, and more (e.g., `repo.find_by(age__gt=18)`).
- **Native Pydantic Support:** Pass Pydantic DTOs directly to `create` and `update` methods. The repository handles the conversion and data extraction automatically.
- **Fully Typed:** Built with Python `typing` and `Generic` types. Enjoy perfect IDE autocompletion and static type checking.
- **Zero Coupling:** Keeps your business logic (Services/Controllers) completely independent from SQLAlchemy's `Session` mechanics.

## 📦 Installation

*(Note: Once published to PyPI, you will be able to install it via pip. For now, you can install it locally.)*

``` bash 
pip install -e .
```

#Quick Start

**1. Define your SQLAlchemy Model**
```from sqlalchemy import Column, Integer, String, Boolean  
from sqlalchemy.orm import declarative_base
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    age = Column(Integer)
    is_active = Column(Boolean, default=True)

```
**2. Create a Repository for your Model**
```from lansuSql.base import BaseRepository

class UserRepository(BaseRepository[User]):
    # You can add custom methods here if needed, 
    # but all standard CRUD operations are inherited automatically!
    pass 
```

**3. Use it in your Application (e.g., FastAPI)**
```from fastapi import Depends
from sqlalchemy.orm import Session
from .database import get_db

# Example Pydantic DTO
from pydantic import BaseModel
class UserCreateDTO(BaseModel):
    name: str
    age: int

def create_user(dto: UserCreateDTO, db: Session = Depends(get_db)):
    repo = UserRepository(model=User, session=db)
    
    # Pass the DTO directly! 
    # Auto-commit=True saves it to the database immediately.
    new_user = repo.create(dto, auto_commit=True)
    return new_user
```

**Dynamic Filtering (find_by)** 
The crown jewel of lansuSql is its dynamic filtering capability. You can use magic operators to build complex queries effortlessly:

```repo = UserRepository(User, db)

# Find exact matches
admins = repo.find_by(is_active=True, role="ADMIN")

# Find with operators (Greater than)
adults = repo.find_by(age__gt=18)

# Find with multiple conditions (Less than or equal + Exact match)
young_actives = repo.find_by(age__lte=25, is_active=True)

# Find in a list of values
selected_users = repo.find_by(id__in=[1, 5, 10])
```

## Supported Operators:

- **__eq:** Equal (Default if no operator is passed)
- **__neq:** Greater than
- **__gt:** Greater than or equal to
- **__gte:** Less than
- **__lt:** Less than or equal to
- **__lte:** In a given list
- **__in:** In a given list
- **__nin:** Not in a given list


## API Reference:
- **get_by_id(id):** Retrieves a single record by its primary key.
- **list_all():** Retrieves all records in the table.
- **find_by( **kwargs**):** Returns a list of records matching the dynamic filters.
- **create(obj_in, auto_commit=False):** Creates a new record from a dict or Pydantic DTO.
- **update(instance, obj_in, auto_commit=False):** In a given list Updates an existing record using a dict or Pydantic DTO. Ignores unset fields automatically.
- **delete(instance, auto_commit=False):** Deletes the record from the database.
- **save(instance, auto_commit=False):** Manually adds and commits an SQLAlchemy instance to the session.

## 🧪 Runing Test

The library is fully tested using pytest and an in-memory SQLite database to ensure reliability.

```Bash
pip install pytest
pytest -v
```

# 📄 License
This project is licensed under the MIT License.

