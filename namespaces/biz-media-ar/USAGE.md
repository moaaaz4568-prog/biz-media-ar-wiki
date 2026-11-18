# USAGE — دليل الاستخدام العملي لويكي biz-media-ar

هذا دليل تشغيلي لويكي المعرفة `biz-media-ar` (موضوعان مبنيان: `sales-outbound` و`wiki-building`). الشاهد الوحيد للحقيقة هو ملفات `sources/`؛ وكل طبقة أعلى منها (ذرات `T_`، مسارد `G_`، مفاهيم `C_`، توترات `X_`، ماسترز `M_`) تجميعٌ يستند إليها بالاقتباس الحرفي. الأوامر أدناه تُنسخ كما هي من جذر المستودع (`repos/knowledge-forge`)، وقد جرى تشغيل كلٍّ منها فعلاً على هذه الويكي.

## 1. كيف تسأل الويكي — وضع السؤال (QUESTION)

السؤال يريد حقيقة محددة («ما سقف الكلمات؟»). المسار: استرجاع ← استشهاد ← جواب من المقاطع المسترجعة فقط.

```bash
python3 tools/forge.py ask "ما هو تسعير القيمة كما يعرّفه المصدر؟" --namespace biz-media-ar
```

إن لم يكن نموذج اللغة متاحاً تعمل الأداة في «درجة الاسترجاع فقط» وتقول ذلك صراحة، مع المقاطع والاستشهادات بلا نثر:

```bash
python3 tools/forge.py ask "ما هو تسعير القيمة كما يعرّفه المصدر؟" --namespace biz-media-ar --no-llm
```

للاسترجاع المباشر (بدون طبقة توليد) استخدم محرك البحث. مثال حقيقي وأول مخرجاته:

```bash
python3 tools/retriever.py search "ما هو تسعير القيمة كما يعرّفه المصدر؟" -k 10 --namespace biz-media-ar
```

```text
engine: {"retrieval": "keyword", "dense": null, "fusion": null, "rerank": null}
 1. [12.781] concepts/sales-outbound/C_price_after_value.md · sales-outbound · concept
     # الأدلة
     - "تسعير القيمة هو شرح ما قد تعنيه النتيجة للعميل قبل عرض الرقم، مع إبقاء الحساب مثالاً مشروطاً لا وعداً مالياً." — sources/S_cpt_CPT_CURATED_SALES_VALUE_PRICING.md ...
```

**تفسير المخرجات:**
- سطر `engine:` يخبرك بأي درجة تشغيل عملت (هنا `keyword`؛ وتصبح `hybrid` مع اسم النموذج الكثيف في `dense` عند تفعيله) — الأداة لا تتحول صامتة أبداً.
- الترتيب `[12.781]` هو درجة BM25 للمقطع؛ يليه المسار ثم الموضوع ثم الطبقة، ثم العنوان داخل الملف ثم مقتطف.
- إن لم يطابق أي مقطع، يطبع المحرك `not in the sources (no chunk matched the query)` ويعيد رمز خروج 1.

للتضييق على موضوع أو طبقة (الطبقات المتاحة لعمود `--layer`: atom, concept, glossary, master, source, synthesis, tension):

```bash
python3 tools/retriever.py search "استهداف" --topic sales-outbound --layer concept -k 5 --namespace biz-media-ar
```

للسؤال العريض أو عند توفر المتجهات الكثيفة (الأعلام الثلاثة موجودة في `argparse` الخاص بـ`retriever.py`):

```bash
python3 tools/retriever.py search "كيف يصف المصدر الاستهداف الجيد؟" --engine hybrid --rerank --expand --namespace biz-media-ar
```

- `--engine hybrid` يدمج BM25 مع البحث الكثيف (فيوجن RRF افتراضياً)، ويعود إلى `keyword` مع التصريح بذلك إن كانت درجة dense معطلة.
- `--rerank` يعيد ترتيب النتائج بمُعاد ترتيب cross-encoder.
- `--expand` يوسّع كل نتيجة إلى قسمها الكامل — للأسئلة العريضة.

## 2. وضع المهمة (TASK): اسأل الويكي أن تنفّذ

المهمة تريد من النموذج أن يصبح المختص ويُنفّذ («خطط حملة»، «اكتب خطة عمل»). المسار: `route` ← قراءة الماسترز المرجعة **كاملة** ← التنفيذ منها فقط. مثال حقيقي بمهمة بيعية واقعية:

```bash
python3 tools/retriever.py route "خطط حملة تواصل خارجي باردة لوكالة إعلامية من شخص واحد وحدد كيف أعرض التسعير على العميل" -m 3 --namespace biz-media-ar
```

مخرجاته الفعلية (مختصرة):

```text
TASK ROUTE — read these masters IN FULL, in this order:

1. masters/sales-outbound/M_sales_hub.md  [103.8]
   question: كيف أبني نظام مبيعات خارجي لوكالة شخص واحد؟
   L0 · 2064 words
   matched: ملخص (TL;DR), النظام 4: التشخيص قبل الحل (Diagnose before Solution), النظام 5: التسعير بعد القيمة (Price after Value)
2. masters/wiki-building/M_wiki_hub.md  [27.4]
   question: كيف نبني ويكي معرفة بالدليل أولاً؟
   L0 · 2001 words
   matched: قالب 2: قالب دورة عمل موثقة, ...

then execute the task using ONLY what these masters say,
citing sources for every claim, and saying "not in the sources"
for anything they do not cover.
```

**تفسير المخرجات:**
- الرقم `[103.8]` مجموع درجات مقاطع الماستر المطابقة للمهمة؛ الترتيب تنازلي به، ويُقدَّم الماستر المحوري (hub) على غيره عند تساوي الدرجة.
- `question:` سؤال الماستر المسجل في front-matter — إن لم يكن سؤال الماستر مرتبطاً بمهمتك فالمهمة على الأرجح خارج الموضوع (انظر القسم 4).
- `L0` مستوى الماستر، و`2064 words` حجمه؛ `matched:` العناوين الداخلية التي طابقت المهمة — بها تحكم مدى الصلة.
- `-m 3` يحدد أقصى عدد ماسترز يُعاد (الافتراضي 3).

لتنفيذ المهمة بأمر واحد (يوجّه، يقرأ الماسترز كاملة، ينفّذ، ويحفظ إيصالاً تحت `.kforge/receipts/`):

```bash
python3 tools/forge.py do "خطط حملة تواصل خارجي باردة لوكالة إعلامية من شخص واحد وحدد كيف أعرض التسعير على العميل" --namespace biz-media-ar
```

وفي بيئة بلا نموذج لغة (تطبع الماسترز المرشدة وتتوقف):

```bash
python3 tools/forge.py do "خطط حملة تواصل خارجي باردة لوكالة إعلامية من شخص واحد وحدد كيف أعرض التسعير على العميل" --namespace biz-media-ar -m 3 --no-llm
```

## 3. كيف تقرأ الماستر المُعاد

- **اقرأه كاملاً وبالترتيب المعاد** — الماستر «مختص في ملف واحد»، لا يُقرأ مقاطع منتقاة. ابدأ بالـhub إن وُجد.
- **افهم ترويسته أولاً** (front-matter): `question:` السؤال الذي يجيب عنه؛ `master_level:` (هنا `L0`)؛ `status: complete` يعني أنه اجتاز البوابات وراجعه إنسان؛ `built_from_hash:` بصمة حالة مفاهيم الموضوع لحظة بنائه — إن تغيرت المفاهيم بعدها تصبح بوابة M9 `STALE` ويطالبك بإعادة البناء.
- **أقسام ماستر L0 في هذه الويكي** (متحقق منها في الملفين): ملخص (TL;DR) ← الأنظمة والكيفية (Systems & how-to) — الكثيف، ≥40% من الكلمات ← التوترات ← التحليل المستقل ← قوالب جاهزة ← فهرس المفاهيم. كل وصفة how-to تنتهي بسطر «متى تنكسر»، وكل ادعاء يحمل اقتباساً حرفياً بمسار مصدره.
- **فهرس المفاهيم في آخر الماستر** يوصلك لكل مفاهيم الموضوع بروابط `[[C_...]]` حقيقية (بوابة M5 ترفع أي رابط ميت).
- عند التعارض بين طرفين، يعرض الماستر التوتر (`X_`) بجانب المتغير الفاصل بين الطرفين — لا يختار بصمت.

## 4. متى تقول «الموضوع غير مبني»

- **الحالة الصريحة:** حين لا يطابق أي ماستر المهمة، يطبع `route` رسالة الرفض حرفياً ويعيد رمز خروج 1:
  ```text
  no master matches this task — the topic may not be built yet
  ```
  وأمر `do` يقول الشيء نفسه مع اقتراح طريق البناء:
  ```text
  no master matches this task — the topic is not built yet.
  propose building it first: sources -> atoms -> concepts -> master (docs/MASTER_GUIDE.md), then re-run.
  ```
  حينها الجواب الصحيح: أعلن أن الموضوع غير مبني، واقترح بناءه بالسلسلة (مصادر ← ذرات ← مفاهيم ← ماستر) — لا ترتجل جواباً من ذاكرتك التدريبية.

- **الحالة الخادعة (مهمة):** المحرك معجمي، فقد يعيد نتائج ضعيفة لمهمة خارج الموضوع لمجرد اشتراك كلمات عامة. جرّبنا فعلاً مهمة مطبخ بحري فرجّعت الماسترز بدرجات متدنية (27.2 و11.2 مقابل 103.8 لمهمة بيعية حقيقية). القاعدة العملية: **لا تكتفِ بوجود مخرجات** — افحص `matched:` وسؤال الماستر؛ فإن كانت المهمة خارجة عن `sales-outbound` و`wiki-building` فاعتبرها غير مبنية وقل ذلك. الأمر نفسه ينطبق على وضع السؤال: المطابقة اللفظية الضعيفة ليست دليلاً (docs/RETRIEVAL.md، الخطوة 10) — فإن لم يحوِ المقطعُ المسترجَع جوابَ السؤال فعلاً فالجواب «not in the sources».

## 5. كيف تضيف مصدراً جديداً — الترتيب الإلزامي والبوابات

الترتيب الإلزامي كما يحدده الكود (AGENT.md خطوةً خطوة، وAGENTS.md: «Build order: glossary FIRST, then atoms, concepts, tensions, masters»، وتعليق `cmd_build` في forge.py: «glossary FIRST — v2 §3 layer 1»):

**S_ ← G_ ← T_ ← C_ ← X_ ← M_** (ثم `Y_` توليف اختياري يقرأ بعد الماسترز لا بدلاً منها).

ملاحظة مهمة عن الأوامر: أوامر البوابة لملفٍّ واحدٍ متاحة في `gates.py` لطبقتين فقط — `concept` و`master` (كما في AGENT.md). طبقات `G_` و`T_` و`X_` لا تملك أمراً فردياً؛ بواباتها (G1–G2، T1–T4، X1–X4) تعمل ضمن فحص `check` الشامل. إليك السلسلة كاملة على المثال الحقيقي القائم (تسعير القيمة):

1. **لقطة Git قبل أي تغيير جماعي** (AGENT.md، الخطوة 0):
   ```bash
   git add -A && git commit -m "snapshot قبل إضافة مصدر جديد"
   ```
2. **S_ — الإدخال:** ضع الملف في `sources/` بترويسة `type: source` و`topic:` و`origin:` و`words:` (على نمط `S_wkt_pro.md` الموجود)، وسجّله في `sources/INDEX.md` (الاسم، الموضوع، عدد الكلمات). المصادر شهود للقراءة فقط — لا تحررها أبداً، وما يبدو خارج الموضوع يُنقل إلى `rejected/` لا يُحذف.
3. **G_ — المسرد أولاً:** لكل مصطلح ملف في `glossary/<topic>/G_name.md` بترويسة `type: glossary` و`aka:` و`origin:`، وقسم «المثال الحي» باقتباس حرفي من المصدر (بوابة G2 تفحصه byte-exact). البوابة:
   ```bash
   python3 tools/gates.py check --namespace biz-media-ar
   ```
4. **T_ — الذرات:** اقتباسات حرفية مفردة في `atoms/<topic>/T_name.md`، لكل اقتباس عنوان `# T_<name>_NN` وسطر `"..." — sources/S_x.md`، بلا أي تفسير (بوابة T4). البوابة نفسها:
   ```bash
   python3 tools/gates.py check --namespace biz-media-ar
   ```
   وتفاصيل التحذيرات (WARN) عند الحاجة:
   ```bash
   python3 tools/gates.py check --namespace biz-media-ar -v
   ```
5. **C_ — المفاهيم:** حوّل عناقيد الذرات إلى `concepts/<topic>/C_name.md` (تعريف + آلية ≥40 كلمة + حدود ≥3 + ≥3 اقتباسات حرفية). البوابة الفردية من جذر المستودع:
   ```bash
   python3 tools/gates.py concept namespaces/biz-media-ar/concepts/sales-outbound/C_price_after_value.md
   ```
   أو من جذر الـnamespace نفسه (المسار النسبي الذي يعمل فعلاً):
   ```bash
   cd namespaces/biz-media-ar && python3 ../../tools/gates.py concept concepts/sales-outbound/C_price_after_value.md
   ```
   `REJECTED` يعني أصلح الملف لا البوابة. أعد البوابة بعد كل تعديل على الملف.
6. **X_ — التوترات:** عند تعارض مفهومين أو مصدرين أنشئ `tensions/<topic>/X_name.md` يعرض الطرفين باقتباسات حرفية ومتغيراً فاصلاً (بوابات X1–X4 عبر `check`؛ لا تحل التعارض بصمت أبداً).
7. **بوابة اكتمال الموضوع** (AGENT.md، الخطوة 6): لا تبنِ ماستر موضوع قبل أن يكون كل مصدر فيه قد أنتج ذرات ومفاهيم.
8. **M_ — الماستر:** `masters/<topic>/M_name.md` بمستوى L0 (6 أقسام / 2000 كلمة على الأقل، how-to ≥40%، تحليل مستقل ≥300 كلمة — العتبات في `config.yml`). البوابة الفردية:
   ```bash
   python3 tools/gates.py master namespaces/biz-media-ar/masters/sales-outbound/M_sales_hub.md
   ```
   ثم مراجعة إنسانية، ثم `status: complete` وسطر مؤرخ في `LOG.md` (بوابة M8 تتحقق من الاثنين).
9. **تحقق أن كل بوابة قابلة للفشل** (قاعدة D8 — شغّلها عند تغيّر الأداة أو القواعد):
   ```bash
   python3 tools/gates.py self-test
   ```

## 6. إعادة الفهرسة والتحقق

الفهرس بيانات مشتقة (`.kforge/` مستثنى من git) — أعد بناءه بعد أي إضافة أو تعديل:

```bash
python3 tools/retriever.py index --namespace biz-media-ar
```

الفهرسة تزايدية ببصمة sha1 لكل ملف (غير المتغير لا يُعاد تقطيعه)؛ لإعادة بناء كامل من الصفر:

```bash
python3 tools/retriever.py index --force --namespace biz-media-ar
```

للاطلاع على إحصاءات الفهرس وحده:

```bash
python3 tools/retriever.py status --namespace biz-media-ar
```

ثم المزامنة الكاملة: بناء الخط مع البوابات وكل طبقة (يتوقف مسمياً الملف المرفوض):

```bash
python3 tools/forge.py build --namespace biz-media-ar
```

والتحقق الشامل بأمر واحد — بوابات + اختبارات وحدات + تقييم recall لكل namespace + اختبار تسرب بين الnamespaces:

```bash
python3 tools/forge.py verify
```

مخرجاته الفعلية آخر تشغيل: ثمانية فحوصات كلها PASS (self-test للبوابات 26/26، فحص البوابات 81 كياناً 0 مرفوض، اختبارات الوحدات 22/22، تقييم recall@10 للأسماءبيس الثلاثة ذات الأسئلة، اختبار تسرب 3×3، وتخطي الscaffold بلا أسئلة). إن فشل أي فحص يظهر `[FAIL]` أمامه باسمه — أصلح المصدر ثم أعد.

نظرة عامة على ما هو مبني في كل namespace:

```bash
python3 tools/forge.py status
```

**قياس الاسترجاع قبل أي توسعة** (لا توسّع الويكي قبل أن يجتاز اختبار الأسئلة المعروفة الإجابة — انظر `eval/EVAL_REPORT.md`):

```bash
python3 tools/evalrun.py -k 10 --namespace biz-media-ar
```

```bash
python3 tools/evalrun.py --compare-engines --namespace biz-media-ar
```

## 7. درجة التضمين الكثيف (اختيارية، متعطلة حالياً في هذه البيئة)

الويكي تعمل بالكامل على BM25 بمكتبة Python القياسية فقط. درجة dense تحتاج `pip install onnxruntime tokenizers sqlite-vec`، وتُبنى بهذين الأمرين الموثقين في AGENTS.md:

```bash
python3 tools/embed.py info
```

```bash
python3 tools/embed.py index --namespace biz-media-ar
```

(وتنزيل النموذج المحلي عند غيابه: `python3 tools/embed.py download e5-small`). عند تشغيل آخر لـ`embed.py info` كانت الحالة: `e5-small READY` محلياً بينما `onnx stack MISSING` و`sqlite-vec MISSING` — لذا تعمل الأوامر حالياً بدرجة keyword وتصرّح بذلك في سطر `engine:`، ومخزن المتجهات القائم (`1019` متجهاً × 384، نموذج e5-small) ينتظر إعادة تثبيت الاعتماديات ليُعاد استخدامه.

## 8. وضعان إضافيان

الجراف العلائقي (أسئلة «من يرتبط بمن ولماذا») — آخر تشغيل: 89 عقدة و43 حافة، رابط واحد غير محلول موثق في `graph/GRAPH.md`:

```bash
python3 tools/forge.py graph --namespace biz-media-ar
```

رادار التناقضات — يقترح مسودات `X_` فقط، والقرار إنساني دائماً:

```bash
python3 tools/forge.py radar --namespace biz-media-ar
```
