/**
 * Copy for the account / plans / payment / sharing UI (2026-11: Telegram
 * bot + paid plans). Montenegrin, Serbian and Bosnian share the Latin "mne"
 * set here - the differences in this copy are a letter or two.
 */

import type { Lang } from './productMatrix';

type Base = 'ukr' | 'rus' | 'eng' | 'mne';

const BASE_OF: Record<Lang, Base> = { ukr: 'ukr', rus: 'rus', eng: 'eng', mne: 'mne', srb: 'mne', bos: 'mne' };

const TEXT = {
  account: { ukr: 'Акаунт', rus: 'Аккаунт', eng: 'Account', mne: 'Nalog' },
  plan: { ukr: 'Тариф', rus: 'Тариф', eng: 'Plan', mne: 'Paket' },
  planFree: { ukr: 'Безкоштовний', rus: 'Бесплатный', eng: 'Free', mne: 'Besplatni' },
  planCompare: { ukr: 'Порівняння', rus: 'Сравнение', eng: 'Compare', mne: 'Poređenje' },
  planGold: { ukr: 'Gold', rus: 'Gold', eng: 'Gold', mne: 'Gold' },
  until: { ukr: 'до {date}', rus: 'до {date}', eng: 'until {date}', mne: 'do {date}' },
  forever: { ukr: 'безстроково', rus: 'бессрочно', eng: 'no expiry', mne: 'bez isteka' },
  upgrade: { ukr: 'Оформити тариф', rus: 'Оформить тариф', eng: 'Get a plan', mne: 'Izaberi paket' },
  telegram: { ukr: 'Telegram', rus: 'Telegram', eng: 'Telegram', mne: 'Telegram' },
  connectTelegram: { ukr: 'Підключити Telegram', rus: 'Подключить Telegram', eng: 'Connect Telegram', mne: 'Poveži Telegram' },
  connectedAs: { ukr: 'Підключено: {name}', rus: 'Подключено: {name}', eng: 'Connected: {name}', mne: 'Povezano: {name}' },
  disconnect: { ukr: 'Відключити', rus: 'Отключить', eng: 'Disconnect', mne: 'Prekini vezu' },
  confirmInTelegram: {
    ukr: 'Підтвердіть у Telegram — бот відкрився в новій вкладці.',
    rus: 'Подтвердите в Telegram — бот открылся в новой вкладке.',
    eng: 'Confirm in Telegram — the bot opened in a new tab.',
    mne: 'Potvrdite u Telegramu — bot se otvorio u novoj kartici.',
  },
  openBotAgain: { ukr: 'Відкрити бота ще раз', rus: 'Открыть бота ещё раз', eng: 'Open the bot again', mne: 'Ponovo otvori bot' },
  linkFailed: {
    ukr: 'Цей Telegram уже прив’язаний до іншого акаунта.',
    rus: 'Этот Telegram уже привязан к другому аккаунту.',
    eng: 'This Telegram is already linked to another account.',
    mne: 'Ovaj Telegram je već povezan sa drugim nalogom.',
  },
  expired: { ukr: 'Час вийшов — спробуйте ще раз.', rus: 'Время вышло — попробуйте ещё раз.', eng: 'Timed out — please try again.', mne: 'Vrijeme je isteklo — pokušajte ponovo.' },
  addCredentials: { ukr: 'Додати email і пароль', rus: 'Добавить email и пароль', eng: 'Add email and password', mne: 'Dodaj email i lozinku' },
  credentialsHint: {
    ukr: 'Щоб входити на сайт і без Telegram.',
    rus: 'Чтобы входить на сайт и без Telegram.',
    eng: 'To log in to the website without Telegram too.',
    mne: 'Da biste se prijavljivali i bez Telegrama.',
  },
  emailTaken: {
    ukr: 'Цей email уже зареєстрований — увійдіть ним і підключіть Telegram там, акаунти об’єднаються.',
    rus: 'Этот email уже зарегистрирован — войдите с ним и подключите Telegram там, аккаунты объединятся.',
    eng: 'This email is already registered — log in with it and connect Telegram there; the accounts will be merged.',
    mne: 'Ovaj email je već registrovan — prijavite se njime i tamo povežite Telegram, nalozi će se spojiti.',
  },
  save: { ukr: 'Зберегти', rus: 'Сохранить', eng: 'Save', mne: 'Sačuvaj' },
  logout: { ukr: 'Вийти', rus: 'Выйти', eng: 'Log out', mne: 'Odjavi se' },
  admin: { ukr: 'Адмінка', rus: 'Админка', eng: 'Admin', mne: 'Admin' },
  error: { ukr: 'Щось пішло не так.', rus: 'Что-то пошло не так.', eng: 'Something went wrong.', mne: 'Nešto nije u redu.' },

  plansTitle: { ukr: 'Тарифи', rus: 'Тарифы', eng: 'Plans', mne: 'Paketi' },
  compareDesc: {
    ukr: 'Ціни всіх магазинів поруч — одразу видно, де найдешевше.',
    rus: 'Цены всех магазинов рядом — сразу видно, где дешевле.',
    eng: 'Every store’s price side by side — see at once where it’s cheapest.',
    mne: 'Cijene svih prodavnica uporedo — odmah se vidi gdje je najjeftinije.',
  },
  goldDesc: {
    ukr: 'Порівняння + списки покупок, якими можна ділитися з рідними.',
    rus: 'Сравнение + списки покупок, которыми можно делиться с близкими.',
    eng: 'Compare + shopping lists you can share with family.',
    mne: 'Poređenje + liste za kupovinu koje možete dijeliti sa porodicom.',
  },
  bothPlaces: {
    ukr: 'Тариф діє і на сайті, і в Telegram-боті. Безкоштовно — ціни одного магазину за раз.',
    rus: 'Тариф действует и на сайте, и в Telegram-боте. Бесплатно — цены одного магазина за раз.',
    eng: 'Plans work on the website and in the Telegram bot. Free: one store’s prices at a time.',
    mne: 'Paket važi na sajtu i u Telegram botu. Besplatno — cijene jedne prodavnice odjednom.',
  },
  perMonth: { ukr: 'на місяць', rus: 'в месяц', eng: 'a month', mne: 'mjesečno' },
  payStars: { ukr: 'Оплатити {stars} ⭐', rus: 'Оплатить {stars} ⭐', eng: 'Pay {stars} ⭐', mne: 'Plati {stars} ⭐' },
  payCard: { ukr: 'Переказ {eur} €', rus: 'Перевод {eur} €', eng: 'Transfer {eur} €', mne: 'Uplata {eur} €' },
  starsNeedTelegram: {
    ukr: 'Оплата зірками йде через Telegram — спершу підключимо ваш Telegram, після підтвердження бот одразу запропонує оплату.',
    rus: 'Оплата звёздами идёт через Telegram — сначала подключим ваш Telegram, после подтверждения бот сразу предложит оплату.',
    eng: 'Stars are paid in Telegram — we’ll connect your Telegram first; once confirmed, the bot offers the payment right away.',
    mne: 'Zvjezdice se plaćaju u Telegramu — prvo povezujemo vaš Telegram, a nakon potvrde bot odmah nudi plaćanje.',
  },
  invoiceOpened: {
    ukr: 'Оплата відкрилася в Telegram. Після оплати оновіть сторінку.',
    rus: 'Оплата открылась в Telegram. После оплаты обновите страницу.',
    eng: 'The payment opened in Telegram. Refresh this page after paying.',
    mne: 'Plaćanje je otvoreno u Telegramu. Nakon plaćanja osvježite stranicu.',
  },
  cardTitle: { ukr: 'Оплата переказом', rus: 'Оплата переводом', eng: 'Bank transfer', mne: 'Plaćanje uplatom' },
  cardSteps: {
    ukr: 'Перекажіть {eur} € за реквізитами нижче й натисніть «Я оплатив». Адміністратор перевірить і ввімкне тариф на 30 днів.',
    rus: 'Переведите {eur} € по реквизитам ниже и нажмите «Я оплатил». Администратор проверит и включит тариф на 30 дней.',
    eng: 'Transfer {eur} € using the details below, then press “I’ve paid”. An admin will check it and turn the plan on for 30 days.',
    mne: 'Uplatite {eur} € prema podacima ispod i pritisnite „Platio sam“. Administrator će provjeriti i uključiti paket na 30 dana.',
  },
  commentPlaceholder: {
    ukr: 'Ім’я відправника або останні 4 цифри картки',
    rus: 'Имя отправителя или последние 4 цифры карты',
    eng: 'Sender name or last 4 digits of the card',
    mne: 'Ime pošiljaoca ili zadnje 4 cifre kartice',
  },
  iPaid: { ukr: 'Я оплатив', rus: 'Я оплатил', eng: 'I’ve paid', mne: 'Platio sam' },
  requestSent: {
    ukr: 'Запит надіслано. Тариф увімкнеться після підтвердження.',
    rus: 'Запрос отправлен. Тариф включится после подтверждения.',
    eng: 'Request sent. The plan turns on once it’s confirmed.',
    mne: 'Zahtjev je poslat. Paket se uključuje nakon potvrde.',
  },
  pendingReview: { ukr: 'Очікує підтвердження', rus: 'Ожидает подтверждения', eng: 'Awaiting confirmation', mne: 'Čeka potvrdu' },
  loginToBuy: { ukr: 'Увійдіть, щоб оформити тариф', rus: 'Войдите, чтобы оформить тариф', eng: 'Log in to get a plan', mne: 'Prijavite se da izaberete paket' },
  login: { ukr: 'Увійти', rus: 'Войти', eng: 'Log in', mne: 'Prijava' },
  currentPlan: { ukr: 'Ваш тариф', rus: 'Ваш тариф', eng: 'Your plan', mne: 'Vaš paket' },
  back: { ukr: '← Назад', rus: '← Назад', eng: '← Back', mne: '← Nazad' },

  chooseStore: { ukr: 'Магазин', rus: 'Магазин', eng: 'Store', mne: 'Prodavnica' },
  freeBanner: {
    ukr: 'Безкоштовно показуємо ціни одного магазину. Порівнюйте всі магазини одразу — від {eur} € або {stars} ⭐ на місяць.',
    rus: 'Бесплатно показываем цены одного магазина. Сравнивайте все магазины сразу — от {eur} € или {stars} ⭐ в месяц.',
    eng: 'Free shows one store’s prices. Compare every store at once — from {eur} € or {stars} ⭐ a month.',
    mne: 'Besplatno prikazujemo cijene jedne prodavnice. Uporedite sve prodavnice odjednom — od {eur} € ili {stars} ⭐ mjesečno.',
  },
  unlock: { ukr: 'Відкрити порівняння', rus: 'Открыть сравнение', eng: 'Unlock comparison', mne: 'Otključaj poređenje' },
  goldRequired: {
    ukr: 'Списки покупок і можливість ділитися ними — у тарифі Gold.',
    rus: 'Списки покупок и возможность делиться ими — в тарифе Gold.',
    eng: 'Shopping lists and sharing them are part of the Gold plan.',
    mne: 'Liste za kupovinu i njihovo dijeljenje su dio Gold paketa.',
  },

  shareTelegram: { ukr: 'Надіслати в Telegram', rus: 'Отправить в Telegram', eng: 'Send via Telegram', mne: 'Pošalji u Telegram' },
  openInBot: { ukr: 'Відкрити в боті', rus: 'Открыть в боте', eng: 'Open in the bot', mne: 'Otvori u botu' },
  sendToUser: { ukr: 'Надіслати користувачу Telegram', rus: 'Отправить пользователю Telegram', eng: 'Send to a Telegram user', mne: 'Pošalji Telegram korisniku' },
  send: { ukr: 'Надіслати', rus: 'Отправить', eng: 'Send', mne: 'Pošalji' },
  sent: { ukr: '✓ Надіслано', rus: '✓ Отправлено', eng: '✓ Sent', mne: '✓ Poslato' },
  userNotFound: {
    ukr: 'Цей користувач ще не запускав @{bot}. Попросіть його відкрити бота або надішліть посилання кнопкою «Надіслати в Telegram».',
    rus: 'Этот пользователь ещё не запускал @{bot}. Попросите его открыть бота или отправьте ссылку кнопкой «Отправить в Telegram».',
    eng: 'This user hasn’t started @{bot} yet. Ask them to open the bot, or send the link with “Send via Telegram”.',
    mne: 'Ovaj korisnik još nije pokrenuo @{bot}. Zamolite ga da otvori bot ili pošaljite link dugmetom „Pošalji u Telegram“.',
  },
  shareMessage: {
    ukr: 'Мій список покупок — відмічайте, що вже купили:',
    rus: 'Мой список покупок — отмечайте, что уже купили:',
    eng: 'My shopping list — tick off what you’ve bought:',
    mne: 'Moja lista za kupovinu — označite šta ste kupili:',
  },

  cheapestTotal: { ukr: 'Найдешевше разом', rus: 'Дешевле всего вместе', eng: 'Cheapest total', mne: 'Najjeftinije ukupno' },

  telegramLogin: { ukr: 'Увійти через Telegram', rus: 'Войти через Telegram', eng: 'Log in with Telegram', mne: 'Prijava putem Telegrama' },
  confirmLoginInTelegram: {
    ukr: 'Підтвердіть вхід у Telegram — бот відкрився в новій вкладці.',
    rus: 'Подтвердите вход в Telegram — бот открылся в новой вкладке.',
    eng: 'Confirm the login in Telegram — the bot opened in a new tab.',
    mne: 'Potvrdite prijavu u Telegramu — bot se otvorio u novoj kartici.',
  },
  or: { ukr: 'або', rus: 'или', eng: 'or', mne: 'ili' },
} as const;

export type AccountTextKey = keyof typeof TEXT;

export function at(lang: Lang, key: AccountTextKey, vars?: Record<string, string | number>): string {
  let text: string = TEXT[key][BASE_OF[lang]];
  if (vars) for (const [k, v] of Object.entries(vars)) text = text.replace(`{${k}}`, String(v));
  return text;
}

export function planLabel(lang: Lang, plan: string): string {
  return at(lang, plan === 'gold' ? 'planGold' : plan === 'compare' ? 'planCompare' : 'planFree');
}

export function formatDate(iso: string, lang: Lang): string {
  const locale = { ukr: 'uk-UA', rus: 'ru-RU', eng: 'en-GB', mne: 'sr-Latn-ME' }[BASE_OF[lang]];
  return new Date(iso).toLocaleDateString(locale);
}
