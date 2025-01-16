#
import os
import logging
import json
import asyncio
import random
from tqdm.asyncio import tqdm

from sqlalchemy.orm import Session

from creator import generate_themes_book, generate_topics_book, generate_book

from utils.tools import write_data_file, read_data_file
from utils.telegram import send_message_admin
from utils.telegra_ph import create_book_in_telegraph

from db.crud import CategoryCRUD
from db.models import SessionLocal, Category, Book

from contextlib import contextmanager
from config import gemini_key


# открывает сессию при обращении с автозакрытием
@contextmanager
def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


class Creator:

    # Функция выбирает тему для книги
    @staticmethod
    async def select_theme(session: Session):
        try:
            cats = session.query(Category).all()
            all_themes = await read_data_file('books/all_themes.json')

            # Создаем список доступных категорий (id которых есть в all_themes)
            available_cat_ids = [int(cat_id) for cat_id in all_themes]
            available_cats = [
                cat for cat in cats if cat.id in available_cat_ids]

            if not available_cats:  # Проверяем, есть ли вообще доступные категории
                return False, False, False

            # Выбираем категорию из доступных
            cat = random.choice(available_cats)
            themes = all_themes.get(str(cat.id), {}).get(
                'themes', [[]])[1]  # Безопасное получение тем

            if themes:
                return random.choice(themes), all_themes, cat

            # Логика повторного выбора, если темы не найдены для выбранной доступной категории.  Не должно срабатывать, но на всякий случай оставил.
            else:
                remaining_cats = available_cats.copy()
                remaining_cats.remove(cat)
                while remaining_cats:
                    cat = random.choice(remaining_cats)
                    themes = all_themes.get(
                        str(cat.id), {}).get('themes', [[]])[1]
                    if themes:
                        return random.choice(themes), all_themes, cat
                    remaining_cats.remove(cat)

                return False, False, False  # Если темы не найдены ни для одной категории

        finally:
            session.close()

    #
    @staticmethod
    async def create_book_in_bd(
        session: Session, user_id: str, name_book: str, content: dict, book_url: str, access_token: str, category_id: int
    ) -> Book:
        try:
            # Создаём книгу
            book = Book(
                user_id=user_id, name_book=name_book, content=content,
                book_url=book_url, access_token=access_token, category_id=category_id
            )
            session.add(book)
            session.commit()
            session.refresh(book)

            return book

        finally:
            session.close()

    # Функция создает темы для книги
    async def auto_themes_creator(session: Session):
        cats = await CategoryCRUD.get_all_categories(session)
        all_themes = {}
        for cat in tqdm(cats, 'Generating themes'):
            themes = await generate_themes_book(cat.name)
            all_themes[cat.id] = {
                "name": cat.name,
                "themes": themes
            }
            await asyncio.sleep(15)

            all_themes_data = json.dumps(
                all_themes, ensure_ascii=False, indent=4)
            await write_data_file(f'books/all_themes.json', all_themes_data)
            return all_themes


# Функция полностью создает книгу
async def auto_book_creator():
    if not gemini_key:
        print(f'GeminiApiKey is None')
        return False
    try:
        with get_session() as session:
            theme, all_themes, cat = await Creator.select_theme(session)
        if theme and all_themes and cat:
            print('Выбрали тему')
            await asyncio.sleep(3)

            qt_topics = random.randint(5, 10)
            result, topics = await generate_topics_book(theme, qt_topics, gemini_api_key=gemini_key)
            print('Получили главы')
            if result:
                await asyncio.sleep(5)
                # генерация книги
                full_book = await generate_book(theme, topics, gemini_api_key=gemini_key)
                print('Получили книгу')
                if full_book:
                    # сохранение книги в файл
                    books_data = json.dumps({
                        'book_name': theme,
                        'books_topics': topics,
                        'full_book': full_book
                    }, ensure_ascii=False, indent=4)
                    # создаем книгу в телеграфе
                    book_url, access_token = await create_book_in_telegraph('Aleks', json.loads(books_data), 'App 5', 'https://t.me/app5_bot')
                    if book_url:
                        print('Загрузили книгу в Telegra.ph')
                        # сохраняем книгу в файл
                        full_books_data = json.dumps({
                            'book_name': theme,
                            'books_topics': topics,
                            'full_book': full_book,
                            'book_url': book_url,
                            'access_token': access_token
                        }, ensure_ascii=False, indent=4)
                        # заносим книгу в папку история для хранения всех книг
                        await write_data_file(f'history/{theme}.json', full_books_data)
                        msg_book = f'📚 <b><a href="{book_url}">{theme}</a></b>'

                        with get_session() as session:
                            # заносим в бд
                            book = await Creator.create_book_in_bd(
                                session, '6316305521', theme, books_data, book_url, access_token, cat.id
                            )

                            if book:
                                print('Сохранили книгу в бд')
                                await send_message_admin(msg_book)

                                # Обновляем файл all_themes.json, удаляя использованную тему
                                try:
                                    all_themes[str(cat.id)]["themes"][1].remove(
                                        theme)
                                    if not all_themes[str(cat.id)]["themes"][1]:
                                        del all_themes[str(cat.id)]
                                    new_all_themes_data = json.dumps(
                                        all_themes, ensure_ascii=False, indent=4)
                                    await write_data_file('books/all_themes.json', new_all_themes_data)
                                    return True

                                except Exception as e:
                                    print(e)
                                    await send_message_admin(f'Ошибка при обновлении файла, темa: <b>{theme}</b>')
                            else:
                                await send_message_admin(f'Не удалось зaписать книгу в бд:\n\n {msg_book}')
                    else:
                        await send_message_admin(f'Не удалось зaписать книгу в телеграф: <b>{theme}</b>')
                else:
                    await send_message_admin(f'Не удалось сгенерировать книгу: <b>{theme}</b>')
            else:
                await send_message_admin(f'Не удалось создать книгу: <b>{theme}</b>')
        else:
            await send_message_admin(f'Не удалось взять темы для: <b>{cat.name}</b>')

    except Exception as e:
        print(e)


# test create
async def main1():
    #
    with get_session() as session:
        theme, all_themes, cat = await Creator.select_theme(session)
        if not any([theme, all_themes, cat]):
            return print('error get theme')
    #
    books_name = 'Sacred Space and the Construction of Reality'
    books_data = {
        "book_name": "Sacred Space and the Construction of Reality",
        "books_topics": [
            "Defining Sacred Space: A Cross-Cultural Exploration",
            "The Phenomenology of Sacred Experience",
            "Architecture of the Divine: Constructing Sacred Buildings",
            "Landscape and the Sacred: Nature as a Site of Divinity",
            "The Body as Sacred Space: Embodiment and Ritual",
            "Sacred Time and the Cyclical Nature of Reality",
            "Symbolism and Representation in Sacred Space",
            "Power, Control, and the Manipulation of Sacred Space",
            "Sacred Space and the Construction of Social Reality"
        ],
        "full_book": {
            "Defining Sacred Space: A Cross-Cultural Exploration": "Defining Sacred Space: A Cross-Cultural Exploration ✨\n\nThe concept of \"sacred space\" is a cornerstone of human experience, yet its definition remains remarkably fluid and multifaceted.  Across cultures and throughout history, humanity has designated certain locations, objects, and even states of being as possessing a heightened significance, a connection to something beyond the mundane.  But what constitutes this \"sacred\"? How is it constructed, perceived, and maintained? This exploration delves into the diverse ways different cultures have defined and interacted with sacred space, revealing both the universality and the unique expressions of this fundamental human impulse.\n\n\n**The Material and the Immaterial:** 🏞️\n\nSacred space isn't always confined to physical locations. While many cultures identify specific geographical sites—mountains, caves, rivers—as sacred, the essence of sacredness often transcends the purely material.  Consider the indigenous traditions of Australia, where the Dreamtime imbues the landscape itself with spiritual significance, transforming the very rocks and trees into manifestations of ancestral stories and power.  Similarly, many religions utilize symbolic objects—a cross, a Torah scroll, a Buddhist stupa—as focal points for sacred experience, transforming the ordinary into the extraordinary through ritual and belief.  These objects act as conduits, facilitating a connection to a transcendent realm.\n\n\n**Ritual and the Creation of Sacredness:** 🕯️\n\nThe act of ritual plays a crucial role in the creation and maintenance of sacred space.  Rituals, whether elaborate ceremonies or simple acts of devotion, serve to demarcate and consecrate a space, transforming it from the profane to the sacred.  Consider the meticulous preparations for a Catholic Mass, the cleansing rites before entering a Shinto shrine, or the intricate sand mandalas created by Tibetan Buddhists. These rituals imbue the space with a palpable sense of the sacred, transforming it into a site for communion with the divine or the ancestral.  The repetition of these rituals further reinforces the sanctity of the space, cementing its significance over time.\n\n\n**Power, Control, and Sacred Space:** 🏰\n\nThroughout history, sacred spaces have often been associated with power and control.  Temples, mosques, and cathedrals have served not only as places of worship but also as centers of political and social influence.  The control over access to and the interpretation of these spaces has often been wielded as a tool of social control.  However, it is important to recognize the resistance to such appropriation.  Many indigenous cultures, for example, have fiercely defended their sacred sites against encroachment and exploitation, demonstrating that the sacred is not merely a passive concept but an active force, a source of both power and resistance.\n\n\n**Sacred Space and the Construction of Identity:** 👥\n\nSacred spaces play a crucial role in shaping collective and individual identities.  They provide a sense of belonging, a connection to a larger community, and a framework for understanding one's place in the world.  Pilgrimages to sacred sites, for example, are often transformative experiences, forging a deeper sense of connection to both the faith and the community.  The shared experience of ritual and devotion within sacred space strengthens social bonds and reinforces a sense of shared identity.  Furthermore, these spaces often serve as repositories of cultural memory, preserving traditions and stories across generations.\n\n\n**The Ongoing Evolution of Sacred Space:** 🌐\n\nThe concept of sacred space is not static. It continuously evolves and adapts in response to changing social, political, and technological contexts.  The rise of virtual reality, for instance, is opening up new possibilities for creating and experiencing sacred space online.  This raises intriguing questions about the nature of sacredness in a digitally mediated world, challenging traditional notions of place and presence.  As we navigate an increasingly interconnected world, understanding the diverse ways in which different cultures define and experience sacred space becomes ever more crucial.  The exploration of sacred space, therefore, is not merely an academic exercise; it is a vital pathway to understanding the human experience itself.\n",
            "The Phenomenology of Sacred Experience": "## Феноменология Священного Опыта\n\n✨  Что делает опыт священным?  Что отличает мимолетное чувство благоговения от глубокого, трансцендентного переживания сакрального?  Эта часть книги исследует феноменологию священного опыта –  его структуру,  составляющие элементы и вариации,  как они проявляются в разных культурах и индивидуальных жизнях.  Мы будем рассматривать священный опыт не как абстрактную концепцию, а как конкретное,  осязаемое переживание,  изучая его через призму человеческого восприятия и сознания.\n\n**Изменение Состояния Сознания:** 🧘‍♀️\n\nМногие священные опыты сопровождаются измененным состоянием сознания (ИСС).  Это не обязательно означает галлюцинации или потерю связи с реальностью.  Скорее, это  *сдвиг* в обычном восприятии,  расширение поля сознания,  ощущение единства с чем-то большим, чем \"я\".  Это может проявляться как:\n\n* **Изменение восприятия времени и пространства:** Время может казаться растянутым или сжатым, границы пространства могут растворяться,  возникает чувство вневременности и безграничности. ⏳\n* **Усиление чувственности:**  Цвета становятся ярче, звуки – глубже, запахи – интенсивнее.  Мир кажется более живым и насыщенным. 🌈\n* **Эмоциональная интенсивность:** Ощущения благоговения,  трепета,  радости,  мистического ужаса  – все они могут быть усилены и обогащены.  ❤️‍🔥\n* **Чувство присутствия:**  Внезапное осознание невидимого присутствия – божества,  духа,  или чего-то сакрального.  🙏\n\n**Символы и Ритуалы:** 🕉️\n\nСвященный опыт редко возникает в вакууме.  Он часто связан с символами и ритуалами,  которые структурируют и направляют его.  Символы – это  *ключи* к сакральному,  они помогают нам соприкоснуться с чем-то трансцендентным.  Ритуалы – это  *действия*,  которые позволяют нам войти в священное пространство и испытать священное время.  Они помогают нам отпустить повседневную рутину и сосредоточиться на сакральном.\n\n\n**Социальный Аспект:** 🫂\n\nСвященные переживания часто разделяются с другими людьми.  Коллективные ритуалы,  молитвы,  песни – все это усиливает священный опыт и формирует чувство общности.  Это создает чувство принадлежности к чему-то большему, чем индивидуальный опыт.\n\n**Разнообразие Опытов:** 🌍\n\nВажно помнить, что священный опыт  *неоднороден*.  Он проявляется в бесчисленных формах,  от созерцания природы до мистического экстаза,  от  глубокой медитации до  коллективного религиозного опыта.  Нет  *единственно верного* способа испытать сакральное.\n\n\n**Влияние на Реальность:** 🤔\n\nСвященный опыт не просто изменяет наше внутреннее состояние.  Он также может трансформировать наше восприятие реальности.  После глубокого сакрального переживания мир может выглядеть иначе,  наши ценности могут измениться,  мы можем увидеть смысл жизни в новом свете.  Это  *перерождение*  изменяет не только наше индивидуальное восприятие, но и влияет на социальное взаимодействие,  формируя коллективные представления о мире и формирование культурных норм.\n\n\n**Заключение:** ✨\n\nФеноменология священного опыта – это обширная и многогранная область исследования.  В этой части мы лишь коснулись некоторых ключевых аспектов.  Дальнейшие исследования потребуют междисциплинарного подхода,  объединяющего антропологию, психологию, нейронауки и теологию.  Однако ясно, что  понимание феноменологии священного опыта –  необходимо для понимания того,  как мы конструируем свою реальность и  взаимодействуем с миром.\n",
            "Architecture of the Divine: Constructing Sacred Buildings": "## Architecture of the Divine: Constructing Sacred Buildings\n\nThe human impulse to create sacred space is as old as civilization itself.  From the megalithic monuments of prehistory to the soaring cathedrals of the Gothic era, the construction of sacred buildings represents a profound attempt to bridge the gap between the earthly and the divine. 🪐  These structures are not merely buildings; they are materialized expressions of belief, potent symbols imbued with spiritual power, meticulously designed to facilitate a connection with the transcendent. ✨\n\n**The Language of Stone and Light:**\n\nThe design of sacred architecture is rarely arbitrary.  Each element – from the orientation of the building to the intricate details of its decoration – speaks a powerful language, carefully crafted to evoke a specific spiritual experience.  Consider, for example, the symbolic use of geometry. 📐 The circle, representing wholeness and infinity, frequently appears in sacred designs, whether in the shape of a mandala, a dome, or a circular enclosure.  Similarly, the square, symbolizing earthly stability and order, often interacts with the circle, creating a complex interplay of earthly and celestial realms.\n\nThe manipulation of light is another crucial aspect. ☀️  The strategic placement of windows, the use of stained glass, or the careful design of skylights can create dramatic effects, flooding the space with divine light, highlighting key elements of the architecture, or even creating symbolic representations of celestial events.  Think of the breathtaking stained glass windows of Chartres Cathedral, transforming sunlight into a radiant tapestry of religious narratives. 🖼️\n\n**Materiality and Meaning:**\n\nThe materials used in the construction of sacred buildings also carry profound symbolic weight.  The choice of stone, wood, or other materials often reflects both the local environment and the spiritual beliefs of the builders.  Stone, for example, often symbolizes permanence and solidity, linking the sacred building to the enduring nature of the divine.  Wood, on the other hand, can evoke a sense of warmth and connection to nature. 🌳  The craftsmanship involved is equally important, often reflecting a dedication to spiritual excellence and a desire to create something truly worthy of the divine presence.\n\n**Sacred Space and the Body:**\n\nSacred buildings are not just about visual symbolism; they are designed to engage the entire human experience. The scale of the architecture, the acoustics of the space, even the scent of incense – all contribute to a multi-sensory experience that can induce feelings of awe, reverence, and spiritual transcendence.  Consider the vastness of a Gothic cathedral, designed to dwarf the human form and evoke a sense of humility before the divine.  Or the hushed silence of a Buddhist temple, encouraging introspection and meditation. 🧘‍♀️\n\n**Beyond the Building:**\n\nThe impact of sacred architecture extends beyond the physical structure itself.  These spaces become focal points for community, fostering a sense of shared identity and purpose. They serve as venues for ritual and ceremony, offering a structured framework for spiritual practice.  Moreover, the very act of constructing a sacred building can be a powerful spiritual act in itself, a collective expression of faith and devotion. 🙏\n\nThe construction of sacred buildings is a complex and multifaceted process, reflecting a profound human desire to create spaces that connect us to the divine.  Through the careful manipulation of geometry, light, material, and the human experience, these buildings transcend their purely functional purpose, becoming powerful symbols of faith and potent catalysts for spiritual transformation. ✨  They are tangible testaments to humanity's enduring quest for meaning and connection with something greater than ourselves.\n",
            "Landscape and the Sacred: Nature as a Site of Divinity": "## Landscape and the Sacred: Nature as a Site of Divinity \n\nThroughout history, humanity has not merely inhabited the landscape, but has actively imbued it with meaning, transforming natural spaces into sacred sites—places where the veil between the mundane and the divine thins.  This deeply ingrained connection between nature and the sacred reflects a fundamental aspect of human consciousness: our inherent need to find the divine in the world around us. 🏞️\n\n### The Earth as a Living Goddess\n\nMany ancient cultures perceived the Earth not as an inert mass, but as a living, breathing entity, a powerful goddess whose moods and cycles mirrored their own lives.  From the fertile bounty of the harvest to the destructive force of earthquakes and volcanic eruptions, the land held both nurturing and terrifying power.  This inherent duality fueled reverence and a profound sense of dependence.  Consider Gaia, the Greek primordial deity representing Mother Earth, or Pachamama, the Andean earth goddess, revered for her ability to both sustain and destroy.  Their worship underscored a recognition of the Earth’s agency and its inextricable link to human existence. 🌎🙏\n\n### Mountains, Rivers, and Forests: Manifestations of the Divine\n\nSpecific natural features often served as focal points for sacred experiences. Mountains, with their imposing presence and connection to the heavens, symbolized the axis mundi, the central point linking the earthly and celestial realms.  🏔️  Their peaks were seen as gateways to otherworldly forces, attracting rituals and pilgrimages aimed at communing with the divine. Rivers, too, held a prominent position, their constant flow representing the cyclical nature of life, death, and rebirth.  🌊  Their waters, often perceived as sacred and cleansing, were the sites of rituals of purification and renewal.  Forests, with their dense canopies and mysterious depths, evoked a sense of awe and mystery, representing the wild, untamed aspects of nature and serving as dwelling places for spirits and deities. 🌳🌲\n\n### The Construction of Sacred Landscapes\n\nHuman intervention played a crucial role in transforming natural landscapes into sacred spaces.  The deliberate placement of monuments, altars, and temples within naturally significant locations amplified their inherent sacredness.  Stone circles, like Stonehenge,  are striking examples of this practice, carefully constructed to align with celestial events, underscoring the cosmic significance of the chosen site.  The act of creating these structures served as a potent form of ritual itself, actively shaping the perceived reality of the space and solidifying its sacred status. ✨\n\n### The Modern Disconnect and the Ongoing Search\n\nThe modern world, with its increasing urbanization and technological advancement, has arguably distanced humanity from this direct connection with nature's sacredness. Yet, the inherent human yearning for the sacred persists.  The enduring appeal of wilderness experiences, the growing interest in eco-spirituality, and the increasing awareness of environmentalism suggest a re-emergence of this ancient connection.  Perhaps our current ecological crisis serves as a potent reminder of the profound interconnectedness between humanity and the natural world, urging us to rediscover the sacred within the landscape and to honor the Earth's inherent divinity. 🌍💚  The re-evaluation and re-sacralization of nature is not merely an aesthetic pursuit but a crucial step in constructing a more sustainable and meaningful reality.\n",
            "The Body as Sacred Space: Embodiment and Ritual": "The Body as Sacred Space: Embodiment and Ritual ✨\n\nThe human body, often overlooked in discussions of sacred space, is perhaps the most intimate and fundamental site of such construction.  It's the primary vessel through which we experience reality, a living temple where the sacred and the profane intertwine.  This chapter delves into the body's role as a sacred space, exploring how embodiment and ritual contribute to our understanding of self and the world around us.\n\n**Embodiment: The Lived Experience of the Sacred** 🙏\n\nOur bodies are not merely biological machines; they are dynamic interfaces between inner and outer realities.  Every sensation, every emotion, every thought is felt *in* the body.  Pain, joy, fear – these are not abstract concepts but visceral experiences rooted in our physical being.  This embodied cognition shapes our perception of the sacred.\n\n*   **Sensory Perception:** The world is experienced through our senses – sight, sound, smell, taste, and touch.  Rituals often engage these senses to create powerful experiences of the sacred.  The scent of incense, the chanting of mantras, the touch of consecrated objects – these sensory inputs shape our emotional and spiritual responses, etching the experience into our embodied memory. 👃👂👅🖐️👁️\n\n*   **Emotional Resonance:** The body is the primary site of emotional expression.  Feelings of awe, reverence, or even terror are physically felt – goosebumps, trembling, a quickening of the pulse.  Rituals often aim to evoke these potent emotions, using them as pathways to connect with the sacred.  Consider the ecstatic dances of Sufi mystics or the profound stillness of meditative practices.  These practices use the body as a conduit for spiritual experience. 💖🔥🧘‍♀️\n\n*   **Mind-Body Connection:** The mind and body are not separate entities but are intricately interwoven.  Our thoughts and beliefs influence our physical state, and conversely, our physical state can profoundly affect our thoughts and emotions. This understanding informs many spiritual traditions, which emphasize the importance of bodily discipline and practices like yoga or tai chi to cultivate inner peace and spiritual awareness. 🧠💪🧘‍♂️\n\n\n**Ritual: Shaping the Body as Sacred Space** 💫\n\nRituals are not merely symbolic actions; they are powerful tools for shaping the body and transforming our relationship with the sacred.  They utilize the body as a medium for enacting and embodying spiritual realities.\n\n*   **Purification Rituals:** Cleansing rituals, from bathing to fasting, are common across many cultures. These practices symbolically and sometimes literally cleanse the body, preparing it to receive the sacred.  They emphasize the importance of physical purity as a prerequisite for spiritual connection. 🚿🧼🌿\n\n*   **Initiation Rites:** Many cultures utilize initiation rituals to mark significant transitions in a person's life (e.g., puberty, marriage, death). These rituals often involve physical transformations – scarification, tattooing, or symbolic clothing – that physically embed the individual's new social and spiritual identity.  The body becomes a living record of these transformative experiences. 🖊️✨⚔️\n\n*   **Performance and Movement:**  Dance, chanting, and other forms of bodily movement are often central to ritual practice.  These movements can express devotion, enact mythological narratives, or induce altered states of consciousness, further reinforcing the body's role as a sacred space.  💃🕺🙏\n\n\n**Conclusion: The Body as a Gateway to the Sacred** 🗝️\n\nThe body is not simply a vessel containing a soul; it is an active participant in the construction of reality, especially in the realm of the sacred.  Through embodiment and ritual, we actively shape our relationship with the divine and the world around us.  Understanding the body as sacred space allows us to appreciate the profound connection between our physical and spiritual selves, revealing the depth and complexity of the human experience.  It is through this intimate engagement with our own embodiment that we ultimately come to understand the sacred within and without.\n",
            "Sacred Time and the Cyclical Nature of Reality": "# Священное Время и Циклическая Природа Реальности ⏳️🌀\n\nМир, который мы воспринимаем, – это не только пространство, но и время.  И так же, как священное пространство структурирует наше восприятие реальности, священное время задает ритм и смысл нашего существования.  Мы не просто существуем *во* времени, мы *внутри* его течения,  определяемого циклами природы, ритуалами и мифами. ✨\n\n## Космические Ритмы и Человеческий Опыт\n\nВне зависимости от культуры, человек всегда осознавал себя частью грандиозного космического цикла.  Вращение Земли вокруг Солнца, фазы Луны, смена времен года – все это естественные ритмы, которые влияют на жизнь человека, на его сельское хозяйство, на его эмоциональное и духовное состояние. ☀️🌕🍂🌱\n\nЭти циклы не просто механистичны; они наполнены смыслом.  Солнце, например, – не только источник тепла и света, но и символ божественной энергии, жизни и возрождения.  Его ежедневный восход и закат символизируют смерть и воскресение, непрерывный круговорот бытия.  Луна, со своими фазами,  часто ассоциируется с женскими циклами, тайнами и магией.  🌑🌕\n\n\n## Время как Миф и Ритуал\n\nЧеловечество создало множество мифов, отражающих циклическую природу реальности.  Мифы о творении и разрушении, о богах и героях,  часто построены вокруг повторяющихся циклов:  возникновение и гибель цивилизаций, вечные битвы света и тьмы.  Эти мифы помогают нам понять наше место в грандиозном космическом спектакле и придают смысл нашей жизни. 🎭✨\n\nРитуалы, в свою очередь,  являются практическим воплощением священного времени.  Ежегодные праздники, связанные с сельскохозяйственными циклами,  или религиозные обряды, повторяющиеся в определенные дни,  подчеркивают связь человека с космическим ритмом.  Они помогают нам ощутить себя частью чего-то большего,  пережить чувство единства с природой и божественным.  🙏🏽🎉\n\n\n## Цикличность как Путь к Трансценденции\n\nПонимание цикличности времени не только расширяет наше мировоззрение, но и открывает путь к трансценденции.  Принимая  неизбежность смерти и возрождения,  мы можем освободиться от страха перед конечностью,  обрести чувство покоя и гармонии.  🌱🕊️\n\nЦиклическая модель времени позволяет взглянуть на жизнь не как на линейную последовательность событий, а как на спираль, где каждый новый виток содержит опыт предыдущего, позволяя нам постоянно совершенствоваться и расти. 🔄️⬆️\n\n\n## Священное Время и Современный Мир\n\nВ быстротечном современном мире, ориентированном на линейный прогресс,  легко забыть о священном времени и его циклической природе.  Однако,  восстановление связи с естественными ритмами,  практика медитации и созерцания,  а также обращение к традиционным ритуалам и мифам,  могут помочь нам обрести чувство равновесия и смысла в жизни.  🧘🏽‍♀️🕰️\n\nЗабывая о циклах, мы теряем связь с глубинной мудростью,  с пониманием того, что мы – часть нескончаемого, вечного потока.  Возвращение к священному времени – это возвращение к себе, к истокам, к пониманию  глубинной взаимосвязанности всего сущего.  🌏❤️\n",
            "Symbolism and Representation in Sacred Space": "## Symbolism and Representation in Sacred Space ✨\n\nSacred spaces, whether grand cathedrals or quiet personal altars, are not merely physical locations; they are potent condensations of meaning, meticulously crafted through symbolism and representation to shape experience and construct reality.  This intricate interplay between the tangible and the intangible is the key to understanding the power these spaces wield.  🙏\n\n**The Language of Symbols:**\n\nSymbols are the fundamental building blocks of sacred space.  They transcend the limitations of language, communicating profound truths and experiences directly to the subconscious. A cross ✝️, for example, signifies faith, sacrifice, and redemption in Christianity, while a mandala 🕉️ in Buddhism represents the cosmos and the interconnectedness of all things.  These symbols are not arbitrary; they are chosen and arranged with deliberate intention, carefully curated to evoke specific emotions, beliefs, and states of being.  The placement of a statue of a deity, the orientation of a building towards a celestial body, the use of specific colors – all are meticulously planned to create a powerful symbolic landscape.\n\n**Visual Representation and Sensory Engagement:**\n\nSacred spaces actively engage the senses to amplify their symbolic impact.  The grandeur of a gothic cathedral, with its soaring arches and stained-glass windows depicting biblical scenes, inspires awe and reverence.  The scent of incense 🌿, the chanting of prayers 🗣️, the soft glow of candlelight 🕯️ – these sensory experiences combine with visual symbols to create a multi-layered, immersive experience.  This holistic approach transforms the space from a mere physical location into a portal to a different reality, a realm where the sacred and the profane intermingle.\n\n**Architecture as Symbolic Expression:**\n\nThe architecture of sacred spaces is itself a powerful form of symbolic representation.  The design, materials, and proportions often reflect underlying cosmological beliefs or spiritual principles.  For instance, the circular shape of some sacred structures symbolizes wholeness and eternity, while the pyramid's pointed apex can represent the connection between the earthly and divine realms.  The use of specific materials, such as stone, wood, or gold, can carry further symbolic weight, reflecting values such as permanence, naturalness, or divine royalty.👑\n\n**The Dynamic Nature of Symbolism:**\n\nIt's crucial to understand that the meaning of symbols within sacred space is not static.  Their interpretation can vary across cultures, religions, and even individual experiences. What might be a symbol of purity in one context could represent something entirely different in another.  Furthermore, the meaning of a symbol can evolve over time, reflecting changes in societal values and beliefs.  The ongoing process of interpretation and re-interpretation is integral to the dynamism of sacred space and its ongoing construction of reality.\n\n**Sacred Space as a Transformative Environment:**\n\nUltimately, the power of symbolism and representation in sacred space lies in its ability to facilitate transformation. By carefully manipulating the visual, auditory, olfactory, and tactile environments, sacred spaces cultivate states of heightened awareness, introspection, and spiritual connection.  They provide a framework for experiencing the sacred, fostering a sense of belonging, community, and ultimately, a deeper understanding of ourselves and our place within the universe. 🌍\n\n\n**Conclusion:**\n\nThe careful orchestration of symbolism and representation is the lifeblood of sacred space.  It's through these carefully chosen elements that these spaces transcend their physical boundaries, becoming powerful loci of meaning and conduits for spiritual experience.  Understanding this intricate interplay is essential for comprehending the profound impact sacred spaces have on the construction of reality, both individually and collectively. ✨\n",
            "Power, Control, and the Manipulation of Sacred Space": "## Власть, Контроль и Манипулирование Священным Пространством 🏛️🗝️\n\n\nСвященное пространство – это не просто место; это сконструированная реальность, обладающая мощной силой, способной формировать убеждения, поведение и даже саму идентичность индивида.  Именно поэтому контроль над священным пространством всегда был источником власти и объектом манипуляции.  Исторически,  контроль над храмами, мечетями, церквями и другими подобными местами обеспечивал доступ к социальному влиянию, политическому могуществу и экономическим ресурсам. 💰👑\n\n\n**Власть через архитектуру и дизайн:** 📐🕍\n\nСама архитектура священного пространства может быть мощным инструментом власти.  Величие собора, внушающая трепет высота минарета,  интимность часовни – все это  создано для того, чтобы вызвать у посетителя определенное состояние: благоговение, смирение, страх или, наоборот,  чувство единения с божественным. 😇 Расположение, освещение, акустика – все подчинено этой цели.  Даже выбор материалов,  цвета и символики тщательно продумываются, чтобы передать  желаемый  посыл и усилить влияние на посетителей.  Например,  использование золота и драгоценных камней подчеркивает богатство и могущество институции, контролирующей это пространство. ✨\n\n\n**Контроль через ритуал и церемонию:**  🙏📿\n\nРитуалы и церемонии, проводимые в священном пространстве,  являются еще одним важным механизмом контроля.  Они структурируют  поведение, устанавливают социальные иерархии и укрепляют  вера в божественное или мистическое.  Соблюдение строгих правил и традиций усиливает ощущение сакральности места и подчиняет участников  ритуала  власти  организаторов.  Повторение ритуалов,  их театральность и использование символов,  манипулируют  эмоциями и формируют убеждения.  Даже  одежда,  язык и  поведение,  регламентированные  ритуалом,   являются  инструментами  контроля.\n\n\n**Манипуляция через символы и иконографию:** 🖼️🌟\n\nСимволы и иконография, используемые в священном пространстве,  могут  не только передавать религиозные или духовные  послания,  но и  манипулировать  восприятием реальности.  Использование определенных образов,  цветов и  геометрических фигур  вызывает  конкретные  эмоциональные  реакции и  формирует  определенные  убеждения.  Например,  использование  креста,  полумесяца или  свастики  вызывает  сильную эмоциональную реакцию  у  верующих,  которая  может  быть  использована  для  управления  поведением.  Этот  метод  часто  применялся  для  поддержания  социального  порядка  и  легитимизации  власти.\n\n\n**Современные формы манипуляции:** 📱💻\n\nВ современном мире контроль над священным пространством принимает новые формы.  Интернет и социальные сети стали новыми платформами для распространения религиозных и духовных  идей,  и  их  использование  также  может  быть  предметом  манипуляции.  Онлайн-сообщества,  виртуальные храмы и  цифровые ритуалы  представляют  новые  возможности  для  контроля  и  манипуляции  сознанием.  Виртуальная реальность открывает  еще  более  широкие  возможности  для  создания  священного  пространства  и  влияния  на  восприятие  реальности.\n\n\n**Осмысление и сопротивление:** 🤔✊\n\nВажно понимать,  как власть,  контроль  и  манипуляция  действуют  в  священном  пространстве.  Только  осознавая  эти  механизмы,  мы  можем  критически  оценить  свои  собственные  убеждения  и  сопротивляться  манипуляциям.  Критическое  осмысление  символики,  ритуалов  и  архитектуры  позволяет  нам  добиться  большей  автономии  и  свободы  в  своем  духовном  опыте.  Осознанное  понимание  священного  пространства  –  это  ключ  к  истинному  освобождению.\n",
            "Sacred Space and the Construction of Social Reality": "## Священное Пространство и Конструирование Социальной Реальности \n\n\nСвященное пространство – это не просто физическое место; это мощный социальный конструкт,  определяющий наши убеждения, ценности и  взаимодействия. ✨  Оно формирует  социальную реальность, создавая  рамки для  поведения,  идентичности и  систему  значений,  объединяющих людей.  Эта  связь между  священным  пространством и  социальной реальностью  является  глубокой и  многогранной.\n\n\n**Создание Коллективной Идентичности:** 🤝\n\nСвященные пространства часто служат  фокусом  для  создания  коллективной  идентичности.  Храмы, мечети, синагоги, церкви – все они  представляют собой  места  собрания, где  люди  чувствуют  себя  частью  чего-то  большего, чем  сами.  Они  укрепляют  чувство  принадлежности,  общности  целей  и  разделяемых  верований.  Ритуалы,  проводимые  в  этих  местах,  дальнейше  подкрепляют  эту  идентичность,  создавая  повторяющиеся  образцы  поведения  и  взаимодействия.\n\n\n**Установление Социальных Норм и Правил:** 📜\n\nСвященные пространства  часто  являются  местом  установления  социальных  норм  и  правил.  Например,  правила  поведения  в  храме  могут  включать  тишину,  уважение,  специфическую  одежду  и  так  далее.  Эти  правила  не  только  регулируют  поведение  внутри  самого  пространства,  но  и  влияют  на  социальное  взаимодействие  в  более  широком  контексте,  формируя  культуру  и  моральные  ценности  общины.  Нарушение  этих  норм  может  повлечь  за  собой  социальное  осуждение  или  даже  наказание.\n\n\n**Легитимация Власти и Иерархий:** 👑\n\nСвященные пространства  могут  служить  для  легитимации  власти  и  иерархий.  Многие  культуры  связывают  своих  лидеров  с  божественным,  наделяя  их  священным  авторитетом.  Церковные  здания,  дворцы  и  другие  монументальные  строения  часто  создавались  для  подчеркивания  такой  связи  и  укрепления  иерархических  структур.  Этот  способ  управления  и  контроля  основан  на  священном  авторитете  и  убеждении  в  божественном  праве  правящей  элиты.\n\n\n**Контроль и Управление:** 👮‍♂️\n\nИнтересно отметить, что священные пространства могут быть использованы не только для создания  гармонии, но и для контроля и управления.  Например,  исключение  определённых  групп  из  доступа  к  священным  местам  может  служить  инструментом  социальной  сегрегации.  Таким  образом,  священное  пространство  может  стать  инструментом  поддержания  существующего  социального  порядка  или  даже  его  изменения,  в  зависимости  от  целей  тех,  кто  контролирует  доступ  к  нему.\n\n\n**Изменения и Трансформации:** 🔄\n\nВажно  понимать,  что  священные  пространства  не  статичны.  Они  могут  изменяться  со  временем,  отражая  сдвиги  в  общественных  ценностях  и  убеждениях.  Это  изменение  может  происходить  как  путем  физической  реконструкции  зданий,  так  и  путем  изменения  ритуалов  и  практик,  проводимых  внутри  этих  пространств.  Изучение  этих  изменений  позволяет  нам  лучше  понять  динамику  взаимодействия  между  священным  пространством  и  социальной  реальностью.\n\n\nВ заключение, священное пространство играет  критическую  роль  в  конструировании  социальной  реальности. Оно  формирует  наши  идентичности,  нормы,  иерархии,  и  даже  способ  контроля  и  управления.  Понимание  этой  сложной  взаимосвязи  поможет  нам  лучше  понять  самих  себя  и  мир,  в  котором  мы  живем. 🙏\n"
        }
    }

    book_url = 'https://telegra.ph/Sacred-Space-and-the-Construction-of-Reality-01-16'
    access_token = '93295906f06015b797edb797818e07887a97b94559880d4082fb0b6262c7'
    category_id = 78
    with get_session() as session:
        try:
            # Создаём книгу
            book = Book(
                user_id='6316305521', name_book=books_name, content=books_data,
                book_url=book_url, access_token=access_token, category_id=category_id
            )
            session.add(book)
            session.commit()
            session.refresh(book)

            return book

        finally:
            session.close()

        # await Creator.create_book_in_bd(
        #     session, '6316305521', books_name, books_data, book_url, access_token, category_id)


# start create
async def main():
    # Включаем логирование
    logging.basicConfig(
        level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'
    )
    await auto_book_creator()


# # старт
if __name__ == "__main__":
    asyncio.run(main())
