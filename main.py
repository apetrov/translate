from fasthtml.common import *
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Boolean

from dataclasses import dataclass

import uvicorn

Base = declarative_base()

class Word(Base):
    __tablename__ = 'words'
    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, index=True)
    language = Column(String, index=True)
    translation = Column(String)
    translation_language = Column(String)

class Db:
    def init_app(app):
        engine = create_engine('sqlite:///data.db')
        Base.metadata.create_all(engine)
        app.db = sessionmaker(bind=engine)()
        return app


def create_input():
    return  Input(name='prompt', id='prompt', placeholder='Enter word', hx_swap_oob='true')

def render(word):
    tid = f'word-{word.id}'
    toggle = A('Toggle', hx_get=f'/words/{word.id}', hx_swap='outerHTML', target_id=tid)
    delete = A('Delete', hx_delete=f'/words/{word.id}', hx_swap='outerHTML', target_id=tid)
    return Li(
            # toggle,
            # delete,
            f"{word.word} in {word.language} is {word.translation} in {word.translation_language}",
            id=tid
            )


@dataclass
class WordRepo:
    db: object

    def all(self):
        return self.db.query(Word).all()

    def get(self, id:int):
        return self.db.query(Word).get(id)

    def save(self, word: Word):
        self.db.add(word)
        self.db.commit()

    def destroy(self, id:int):
        word = self.get(id)
        self.db.delete(word)
        self.db.commit()

@dataclass
class WordForm:
    prompt: str


@dataclass
class WordsController:
    db: object
    openai: object

    def __post_init__(self):
        self.repo = WordRepo(self.db)
        self.translator = OpenAiAdapter(self.openai)

    def show(self, id:int):
        word = self.repo.get(id)
        word.done = not word.done
        self.repo.save(word)
        return render(word)

    def destroy(self, id:int):
        self.repo.destroy(id)

    def index(self):
        words = self.repo.all()
        form = Form(
                Group(
                    create_input(),
                    Button('Add')
                    ),
                hx_post='/words/create',
                target_id='word-list',
                hx_swap='beforeend',
        )

        return Titled("Words",
                Card(
                    Ul( *[render(t) for t in words], id='word-list'),
                    header=form
                ))

    def create(self, word_form: WordForm):
        word = Translate(self.repo, self.translator).translate(word_form)
        return render(word), create_input()

@dataclass
class Translate:
    repo: object
    adapter: object

    def translate(self, word_form):
        data = self.adapter.translate(word_form.prompt)
        word =  Word(**data)
        self.repo.save(word)
        return word

class Routes:
    def init_app(self, app):
        words_controller = WordsController(app.db, app.openai)
        app.route("/words", methods=['get'])(words_controller.index)
        app.route("/words/create", methods=['post'])(words_controller.create)


@dataclass
class OpenAiAdapter:
    openai: object

    def translate(self, prompt):
        import json
        system_prompt = """
            You are an API implementing this code:
            def translate(prompt)->json:
                prompt: str
                    is a word or sequence in any language, most likely English, Russian, Spanish or Catalan.
                    it might contain a language that user wants to translate to.
                    If the language is not provided, you decide the following way:
                    * When it's a word in English, translate it to Russian.
                    * In other cases translate it to English.


                Examples:

                "Rabbit" =>
                {
                    "word": "Rabbit",
                    "language": "English",
                    "translation": "Кролик",
                    "translation_language": "Russian"
                }
            Don't include any codeblocks in the response. Just the JSON object.
        """
        response = self.openai.chat.completions.create(
          model="gpt-4o",
          messages=[
              {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )

        content = (response.choices[0].message.content)
        print(content)
        return json.loads(content)


class Env:
    def init_app(self, app):
        import os
        from openai import OpenAI
        client = OpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
        )
        app.openai = client
        return app

def create_app():
    # doesn't work out of the box
    # app = FastHTML()
    app, rt = fast_app()
    Env().init_app(app)
    Db.init_app(app)
    Routes().init_app(app)
    return app

def main():
    app = create_app()
    uvicorn.run("main:create_app", reload=True, factory=True, host="0.0.0.0")

if __name__ == '__main__':
    main()
