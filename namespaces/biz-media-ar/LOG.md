| Date | What happened | Measured by | Result |
|---|---|---|---|
| 2026-11-16 | إعادة البناء بعد فقد الساندبوكس: 24 مصدر S_ (69,597 كلمة) ثم 19 ذرة T_ (147 اقتباساً) و7 مسارد G_ و4 مفاهيم C_ وتوترين X_ | python3 tools/gates.py check (من داخل namespace) | 49 كيان، 0 مرفوض |
| 2026-11-16 | أسئلة التقييم (14 سؤالاً في 4 طبقات) + قياس BM25 على الـnamespace المُعاد بناؤه | python3 tools/evalrun.py -k 10 (من داخل namespace) | recall@10 = 12/12 = 1.000 (exact 7/7, paraphrase 3/3, comparison 2/2) |
| 2026-11-16 | إعادة تكميل طبقات بالترتيب الإلزامي: T_ 25/25 مصدر، G_ 19 ملفاً (25/25 ذرة)، C_ 10 مفاهيم (تصحيح: كان مكتوباً 11 — 9 في sales-outbound و1 في wiki-building؛ S_wkt_pro سطر برومبت واحد مغطى بـG_pro_prompt)، X_ 3 توترات | python3 tools/gates.py check | 73 كياناً، 0 مرفوض |
| 2026-11-16 | الماسترز L0: M_sales_hub (7 أنظمة، 27 اقتباساً) وM_wiki_hub (6 أنظمة، 22 اقتباساً) مع built_from_hash لكل موضوع | python3 tools/gates.py check | 75 كياناً، 0 مرفوض |
| 2026-11-16 | تضمين كثيف e5-small (989 chunks، 157 ثانية، نموذج محلي خارج المستودع) + مقارنة محركات: keyword وhybrid كلاهما recall@10 = 12/12 = 1.000 (الفائز المسجل: hybrid) | python3 tools/evalrun.py --compare-engines | 1.000 على كل الطبقات |
| 2026-11-17 | جراف الكيانات العلائقي: 83 عقدة (24 S_ + 25 T_ + 19 G_ + 10 C_ + 3 X_ + 2 M_) و42 حافة wiki-link محققة واحدة-واحدة + رابط واحد غير محلول (نص توثيقي hatch_widget داخل backticks — false positive للمستخرج، موثق في GRAPH.md) | python3 tools/forge.py graph --namespace biz-media-ar + تحقق مستقل لكل حافة | 83 عقدة، 42 حافة، 0 حافة كاذبة |
