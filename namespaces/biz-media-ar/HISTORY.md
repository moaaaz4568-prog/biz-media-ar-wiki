# HISTORY — تاريخ بناء ويكي biz-media-ar

> سرد تاريخي مستخرج بالكامل من سجل git الفعلي للمستودع ومن `LOG.md`. كل hash وتاريخ أدناه مأخوذ من `git log` كما هو، وكل وصف لالتزام هو من رسالة الالتزام نفسها؛ لم يُضَف شيء من خارج السجل.

## البداية

أول التزام يلمس `namespaces/biz-media-ar` هو **`abf9ba5` بتاريخ 2026-11-16**، برسالة: «init: biz-media-ar namespace scaffold (rebuild after sandbox recycle)». أنشأ هذا الالتزام الهيكل الأول للويكي في 14 ملفاً (111 سطراً): ملف `config.yml` الذي يضبط قواعد الطبقات كلها (المفهوم بين 250 و600 كلمة بحد أدنى 3 اقتباسات و3 حدود؛ الماستر يتدرج من L0 حتى L3 ولا يُبدأ عالياً؛ الاسترجاع بـ top_k=10 وهدف recall 0.8 ومحرك auto يصبح hybrid عند توفر المتجهات الكثيفة؛ تضمين e5-small بـ384 بُعداً)، وملف `INDEX.md` لكل طبقة (المصادر، الذرات، المسارد، المفاهيم، التوترات، الماسترز، التوليف، الأرشيف، المرفوض، التقييم)، وملف `CANARY-biz-media-ar.md` لفحص تسريب الاسترجاع بين الـnamespaces، وملف `eval/questions.yml` الأولي.

كلمة «rebuild» في رسالة الالتزام ليست عرضية؛ هذه إعادة بناء بعد فقدان بيئة التشغيل السابقة (sandbox recycle)، وهو ما تؤكده رسالة الالتزام التالي مباشرة. بدأت الويكي إذن من هيكل فارغ صباح 2026-11-16، ووصلت إلى ويكي مكتملة ومقاسة في غضون يومين.

## مراحل البناء

بُنيت الطبقات بالترتيب الإلزامي: المصادر أولاً، ثم الذرات، ثم المسارد، ثم المفاهيم، ثم التوترات، ثم الماسترز، ثم الجراف والفهرسة والتقييم. ملاحظة منهجية: عدادات رسائل الالتزامات اختلفت أحياناً عن العد النهائي للملفات وصُححت لاحقاً؛ الأعداد المعتمدة للوضع النهائي هي أعداد `LOG.md` بعد تصحيحات الالتزام `7b8d1a8`.

### المصادر (طبقة S_)

- **`1a5269c` — 2026-11-16**: «intake(rebuild): 24 verbatim S_ sources from surviving handoff+wikimind corpus (69,597 words) after sandbox recycle» — استيعاب 24 مصدراً حرفياً بمجموع 69,597 كلمة مما نجا من مدونة handoff+wikimind، في 25 ملفاً و8,172 سطراً. أضخم ملفين: `S_wkt_conversation-export.md` (4,799 سطراً) و`S_wkt_wiki_all_talk.md` (2,025 سطراً).

### الذرات (طبقة T_)

ثلاثة التزامات في 2026-11-16 رفعت الذرات من الصفر إلى التغطية الكاملة للمصادر؛ تعد رسائلها 19 و4 و1 ملفات، والعدد النهائي المستقر في `LOG.md` هو 25 ذرة:

- **`727bad1`**: «atoms: 19 T_ files (147 verbatim quotes) across sales-outbound + wiki-building — gates 36 entities 0 rejected» — الدفعة الأولى من الذرات عبر الموضوعين (البيع والتواصل الصادر، وبناء الويكي)، ببوابات 36 كياناً منها صفر مرفوض.
- **`326c67b`**: «atoms: 4 more T_ files (followup, multichannel, ops, postreply — 29 quotes) closing S_->T_ coverage gap — 53 entities 0 rejected» — أربع ذرات إضافية تسد فجوة التغطية.
- **`04411d2`**: «atoms: T_conversation_export (14 quotes, 43,931-word source) — S_->T_ coverage now 24/24 = 100%, 54 entities 0 rejected» — ذرة تصدير المحادثة المستخلصة من مصدر من 43,931 كلمة، فاكتملت تغطية المصادر بالذرات.

### المسارد (طبقة G_)

- **`164ab13`** — 2026-11-16: «glossary: 7 G_ files (4 sales-outbound + 3 wiki-building) — gates 43 entities 0 rejected» — أول سبعة مسارد موزعة على الموضوعين.
- **`f47838b`** — 2026-11-16: «glossary: 11 G_ files closing atom coverage (followup, multichannel, ops, postreply, pro_prompt, consultative, positioning, hook, offer, diagnosis, retention, story) — 66 entities 0 rejected, atom coverage 25/25» — دفعة كبيرة سدت ما ظُن أنه آخر فجوة في تغطية الذرات.
- **`7b8d1a8`** — 2026-11-17: «glossary: 6 G_ files completing atom->glossary coverage 25/25 (self-check found '25/25' claim was file-count not coverage; all quotes byte-exact) — corrections: S_=24 (25 counted CANARY), C_=10 — graph rebuilt 89 nodes/42 edges — reindex 1019 chunks + dense 1019x384 — gates 81 entities 0 rejected, engines 1.000, verify PASS» — أهم التزام تصحيحي في تاريخ الويكي: فحص ذاتي كشف أن ادعاء «25/25» السابق كان عدّ ملفات لا تغطية فعلية، فأضاف ستة مسارد تكمل التغطية الحقيقية 25/25، وصحح عدد المصادر إلى 24 (العد السابق 25 كان يشمل ملف CANARY)، وعدد المفاهيم إلى 10، ثم أعاد بناء الجراف (89 عقدة/42 حافة) والفهرسة (1019 chunks ومثلها متجهات كثيفة بـ384 بُعداً).

### المفاهيم (طبقة C_)

أربعة التزامات في 2026-11-16:

- **`fddd1d7`**: «concepts: 4 C_ files (trust, one-person agency, warmup+throttle, evidence-first wiki) — all ACCEPTED» — أول أربعة مفاهيم، جميعها مقبولة بالبوابات.
- **`80f6a86`**: «concepts: 4 C_ files (content funnel, diagnose-first, followup system, measure-then-scale) — 70 entities 0 rejected».
- **`72f1a72`**: «concepts: C_signal_over_spray + C_price_after_value — C_ layer coverage 23/24 (S_wkt_pro is a single prompt line, covered by G_pro_prompt — documented method decision)» — مفهومان أخيران مع قرار منهجي موثق بشأن المصدر المتبقي.
- **`1fc23f9`**: «concepts: fix C8 outgoing links in signal/price concepts — all clean» — إصلاح الروابط الصادرة في بوابة C8 لمفهومي الإشارة والتسعير.

### التوترات (طبقة X_)

- **`0ace6d9`** — 2026-11-16: «tensions: 2 X_ files (value-vs-infrastructure, volume-vs-signal) + INDEX/LOG rows — 49 entities 0 rejected».
- **`4742d42`** — 2026-11-16: «tension: X_persistence_vs_relevance + concepts/tensions INDEX + LOG — layers complete in mandatory order: T_25/25, G_19, C_11, X_3 — 73 entities 0 rejected» — التوتر الثالث الذي أتم الطبقات كلها بالترتيب الإلزامي (الأعداد في الرسالة كما كُتبت يومها؛ صححها الالتزام `7b8d1a8` لاحقاً إلى S_=24 وC_=10).

### الماسترز (طبقة M_)

ثلاثة التزامات في 2026-11-16:

- **`addd00d`**: «master L0 #1: M_sales_hub — 6 sections, 2000+ words, how-to 44%, 27 byte-exact quotes, built_from_hash recorded — 74 entities 0 rejected» — الماستر الأول على مستوى L0، بنسبة إرشاد عملي 44% و27 اقتباساً حرفياً وبصمة built_from_hash مسجلة.
- **`e45abdd`**: «master: fix 3 tension links in M_sales_hub» — إصلاح ثلاثة روابط توتر داخل الماستر.
- **`a17c05c`**: «master L0 #2: M_wiki_hub — 6 systems, 2020 words, 22 byte-exact quotes, built_from_hash — masters INDEX + LOG — 75 entities 0 rejected» — الماستر الثاني، فاكتملت طبقة الماسترز بماستر لكل موضوع.

### الجراف والفهرسة والتقييم

- **`9a23aa0`** — 2026-11-16: «eval: 14 known-answer questions (4 tiers) — BM25 recall@10 = 12/12 = 1.000» — بناء أسئلة التقييم المعروفة الإجابة في أربع طبقات وقياس أول للاسترجاع.
- **`f46b3ff`** — 2026-11-16: «finale: dense e5-small indexed (989 chunks, local model gitignored) + engine comparison keyword=hybrid=1.000 (winner hybrid) + LOG — forge verify PASS 8/8» — خاتمة يوم البناء الأول: تضمين كثيف بـ989 مقطعاً ومقارنة محركات انتهت بتكافؤ 1.000 وتسجيل hybrid فائزاً، وتحقق شامل PASS 8/8.
- **`275481d`** — 2026-11-17: «graph(biz-media-ar): entity graph 83 nodes / 42 verified wiki-link edges + 1 documented false-positive (hatch_widget backtick prose) — graph.json + GRAPH.md + LOG row; LOG correction: C_ 11->10 (INDEX miscount)» — بناء جراف الكيانات العلائقي بملفَي graph.json وGRAPH.md، بتحقق مستقل لكل حافة وربط واحد غير محلول موثق كإيجابية كاذبة للمستخرج.
- **`3b429e1`** — 2026-11-17: «log: reindex after disk restore (85 files -> 995 chunks) + dense e5-small rebuilt (995x384 in gitignored .kforge/vec.db, fully rebuildable) — verify PASS 8/8, engines 1.000» — إعادة فهرسة بعد استعادة القرص (85 ملفاً ← 995 مقطعاً) مع متجهات قابلة لإعادة البناء كاملة من المستودع.
- **`1d74b90`** — 2026-11-17: «log: dense rebuilt after env loss (1019x384, hybrid+rerank 1.000, verify PASS)» — إعادة بناء المتجهات الكثيفة بعد فقد البيئة مرة أخرى (1019 متجهاً × 384 بُعداً) بنتيجة 1.000 على hybrid+rerank.

## الويكي اليوم

الأعداد النهائية كما يقيسها `LOG.md`:

| الطبقة | العدد |
|---|---|
| مصادر S_ | 24 (العد السابق 25 كان يشمل CANARY) |
| ذرات T_ | 25 |
| مسارد G_ | 25 (تغطية الذرات 25/25) |
| مفاهيم C_ | 10 |
| توترات X_ | 3 |
| ماسترز M_ | 2 (M_sales_hub وM_wiki_hub) |

- **الجراف**: 89 عقدة و42 حافة wiki-link محققة واحدة-واحدة، صفر حافة كاذبة، وربط واحد غير محلول موثق كإيجابية كاذبة للمستخرج في GRAPH.md.
- **الفهرسة**: 1019 مقطعاً (chunk) قيد التحديث إلى 1041، مع 1019 متجهاً كثيفاً × 384 بُعداً (نموذج e5-small) في `.kforge/vec.db` المستثنى من git والقابل لإعادة البناء الكاملة من المستودع بأمرين.
- **التقييم**: recall@10 = 1.000 (بالتفصيل: exact 7/7، وparaphrase 3/3، وcomparison 2/2) على محرك hybrid مع rerank؛ و`forge verify` يعيد PASS 8/8.
- **البوابات**: 81 كياناً، 0 مرفوض.
- **وثائق مرافقة**: `USAGE.md` (دليل الاستخدام العملي الكامل)، و`audit/INDEPENDENT_AUDIT.md` (تدقيق مستقل بتاريخ 2026-11-18 بمنهجية قياس مستقلة عن أدوات الويكي)، وملفَي TOPIC.md لموضوعَي طبقة المفاهيم.

## النقلة للريبو الجديد

يوم 2026-11-18 شهد أربعة التزامات autopush تمس الـnamespace، ثم التزاماً خامساً يتوّج الانتقال إلى البيت الجديد:

- **`40ec65b`** (11:59): «autopush: incremental work» — مس 48 ملفاً عبر طبقات الويكي بتغيير أنماط الملفات فقط، دون أي تعديل على المحتوى.
- **`dd46cc8`** (12:09): «autopush: incremental work» — إضافة ملفَي TOPIC.md لطبقة المفاهيم (sales-outbound وwiki-building، 118 سطراً).
- **`2a1d4b0`** (12:24): «autopush: incremental work» — إضافة التدقيق المستقل `audit/INDEPENDENT_AUDIT.md` (86 سطراً).
- **`7ff44d5`** (13:29): «autopush: incremental work» — إضافة `USAGE.md`، دليل الاستخدام العملي للويكي (243 سطراً).
- **`3f4f0d7`** (13:39): «autopush: incremental work» — إعادة كتابة README الرئيسية ليصبح عنوان المستودع «biz-media-ar-wiki — ويكي معرفة عربية مبنية على الدليل».

بهذا اكتملت النقلة من القالب العام: كان الخط الأساسي قد جُوكِر على استنساخ نظيف من الريبو القديم `moaaaz4568-prog/knowledge-forge` بتاريخ 2026-11-15 كما يسجل `LOG.md` الجذري، ثم أصبح remote الأصل للمستودع هو `https://github.com/moaaaz4568-prog/biz-media-ar-wiki.git`، وصار ريبو `biz-media-ar-wiki` على GitHub (حساب moaaaz4568-prog) هو البيت الحالي للويكي بتاريخ 2026-11-18، و`namespaces/biz-media-ar` فيه هو الـnamespace الوحيد الذي يحمل المحتوى المعرفي كله.
