# Мой Косметолог — Project Brief

## Что это
Skincare PWA для российской аудитории. Phase 1: web PWA. Phase 2: KMP mobile (Android + iOS).

## Основной флоу (MVP)
1. **Welcome screen** — название, value prop, CTA «Начать»
2. **Scan upload** — пользователь делает селфи или загружает фото лица
3. **Auth wall** — ВЛАДЕЛЕЦ-РЕШЕНИЕ ОТКРЫТО: после скана или перед quiz? (см. pending decision)
4. **Scan result** — AI-анализ: проблемы кожи с severity, тип кожи, hydration estimate
5. **Personalized routine** — утро/вечер с продуктами под бюджет и тип кожи
6. **Product detail** — карточка продукта с обоснованием выбора
7. **Affiliate redirect** — Wildberries / Ozon / Золотое Яблоко
8. **Progress tracking** — повторный скан через 4 недели, сравнение

## Целевая аудитория (MVP)
**Портрет 1: Алина, 24** — менеджер, проблемы с акне после 23, тратит 5-8К/мес на уход, ходит к косметологу 1-2 раза в год.
**Портрет 2: Денис, 19** — студент, гиперкератоз / acne, бюджет 1-3К/мес, никогда не был у косметолога.

Портреты 3-5 (зрелая кожа, sensitive, гиперпигментация) — Phase 2.

## Принципиальное «не делаем» в MVP
- ❌ Записи к мастерам / косметологам (не бронируем)
- ❌ Прямые покупки внутри приложения (только affiliate)
- ❌ Чат с косметологом / live-консультации
- ❌ Push-нотификации (Phase 1 web → нет push на iOS PWA)

## Phase 2 включает
- KMP mobile (Compose Multiplatform)
- Портреты 3-5
- Возможно: progress photos AI-сравнение
- Возможно: записи к мастерам

## Платформа
Phase 1: Next.js 14 App Router PWA, FastAPI backend, PostgreSQL, Redis, S3-совместимое хранилище (Yandex Object Storage).
Phase 2: + Kotlin Multiplatform shared module, Compose Multiplatform для iOS/Android.
