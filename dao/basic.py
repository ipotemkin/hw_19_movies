# это файл для классов доступа к данным (Data Access Object). Здесь должен быть класс с методами доступа к данным
# здесь в методах можно построить сложные запросы к БД

from errors import NotFoundError, NoContentError, BadRequestError, DatabaseError, ValidationError


class BasicDAO:
    def __init__(self, session, model, schema, nested_schema=None):
        self.session = session
        self.model = model
        self.schema = schema  # if validation needed while creating/updating a record
        self.nested_schema = nested_schema if nested_schema else schema

    def get_all(self, raise_errors=True):
        objs = self.session.query(self.model).all()
        if raise_errors and not objs:
            raise NotFoundError
        return [self.nested_schema.from_orm(obj).dict() for obj in objs]

    def get_one(self, uid: int):
        obj = self.session.query(self.model).get_or_404(uid)
        return self.nested_schema.from_orm(obj).dict()

    def create(self, new_obj: dict):
        if not new_obj:
            raise NoContentError

        # to check whether the new_obj meets the model; it will be unnecessary after DB migration
        try:
            self.schema.parse_obj(new_obj)
        except Exception as e:
            print(f'Error: {e}')
            raise ValidationError

        try:
            obj = self.model(**new_obj)
        except Exception:
            raise BadRequestError

        try:
            self.session.add(obj)
            self.session.commit()
        except Exception:
            raise DatabaseError
        return obj

    def update(self, new_obj: dict, uid: int):
        if not new_obj:
            raise NoContentError

        if ('id' in new_obj) and (uid != new_obj['id']):
            raise BadRequestError

        q = self.session.query(self.model).filter(self.model.id == uid)
        q.first_or_404()  # to test existence of the object

        try:
            q.update(new_obj)
            self.session.commit()
        except Exception:
            raise DatabaseError

    def delete(self, uid: int):
        obj = self.session.query(self.model).get_or_404(uid)
        try:
            self.session.delete(obj)
            self.session.commit()
        except Exception:
            raise DatabaseError

    def get_all_by_filter(self, req: dict):
        if not (res := self.model.query.filter_by(**req).all() if req else self.model.query.all()):
            raise NotFoundError
        return [self.nested_schema.from_orm(obj).dict() for obj in res]
