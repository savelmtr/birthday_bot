class CALLBACK_TEXTS:
    welcome = '''
        Привет! С помощью этого бота можно отслеживать дни рождения участников групп, куда добавлен бот.
        В боте каждый может добавить свои пожелания или интересы.
        По запросу бот проинформирует вас о днях рождения и пожеланиях участников.
    '''
    adder_link = 'Привет! Я -- бот. Я буду хранить информацию о днях рождений участников группы и их интересах.'\
        ' Тех, кто добавился в чат после меня, я отслежу самостоятельно. Ранних пташек приглашаю перейти по ссылке '\
        'https://t.me/{bot_name}/?start={chatid}, чтобы я знал о вашем существовании.'
    groupid_incorrect = '{payload} не является валидным id группы. Попробуйте еще раз!'
    you_ware_added_as_memeber_of_group = 'Вы были отмечены как член группы {chatname}. Когда вы удалитесь из этого чата,'\
        ' бот должен автоматически отследить этот факт и удалить вас из своих записей.'
    info_in_group = 'Ты находишься в группах: {groups}'
    info_wishes = 'Список твоих желаний и интересов: {my_wishes} 🎁'
    info_name = 'Ты представлен как: @{username} ({first_name} {last_name})'
    wishes_updated = 'Пожелания успешно обновлены'
    database_error='Ошибка базы данных при попытке получить информацию о пользователе.'
    change_name_proposal = 'Напишите своё имя и фамилию.'
    change_wishes_proposal = 'Введите ваши интересы и пожелания.'
    your_wishes = '\n На данный момент ваши пожелания: {wishes}'
    name_has_been_changed = 'Имя изменено на {new_name}'
    set_birthday_proposal = 'Введите свой день рождения в формате ГГГГ-ММ-ДД'
    incorrect_birthday = 'Вы ввели некорретную дату дня рождения: {text}. Попробуйте ещё раз.'
    birthday_updated = 'День рождения обновлён ({birthday})'
    my_birthday = 'Твой день рождения: {birthday}'
    cancel_successfull = 'Хорошо, в другой раз.'
    you_participate_no_groups = 'Вы не состоите ни в одной группе 😢'
    choose_chat = 'Выбери чат: \n'
    participants_header = 'Участники группы {groupname}:\n'
    wishes_unavailable = 'Пользователь пока не добавил свои интересы и пожелания.'
    user_unavailable = 'Пользователь отсутствует в группе.'
    wishes_of_user = 'Пожелания и интересы пользователя:\n{f_name} {l_name}\n{wishes}'
    to_check_wishes_press_a_btn = '\n\nЧтобы посмотреть интересы и пожелания участника, нажмите кнопку с номером под сообщением.'
    only_alpha = 'Назовите себя, используя только буквы 😀'
    incorrect_input = 'Принимается только текстовое сообщение 😕'
