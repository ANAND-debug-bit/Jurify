"""SQLAlchemy implementations of the domain repository ports
(app.domain.repositories) — Module 7. Each takes an AsyncSession
(typically from a UnitOfWork, app.database.unit_of_work) via constructor
injection and maps between app.models ORM rows and app.domain.entities.
"""
