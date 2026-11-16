| Date | What happened | Measured by | Result |
|---|---|---|---|
| 2026-11-16 | إعادة البناء بعد فقد الساندبوكس: 24 مصدر S_ (69,597 كلمة) ثم 19 ذرة T_ (147 اقتباساً) و7 مسارد G_ و4 مفاهيم C_ وتوترين X_ | python3 tools/gates.py check (من داخل namespace) | 49 كيان، 0 مرفوض |
| 2026-11-16 | أسئلة التقييم (14 سؤالاً في 4 طبقات) + قياس BM25 على الـnamespace المُعاد بناؤه | python3 tools/evalrun.py -k 10 (من داخل namespace) | recall@10 = 12/12 = 1.000 (exact 7/7, paraphrase 3/3, comparison 2/2) |
| 2026-11-16 | إعادة تكميل طبقات بالترتيب الإلزامي: T_ 25/25 مصدر، G_ 19 ملفاً (25/25 ذرة)، C_ 11 مفهوماً (23/24 مصدر — S_wkt_pro سطر برومبت واحد مغطى بـG_pro_prompt)، X_ 3 توترات | python3 tools/gates.py check | 73 كياناً، 0 مرفوض |
| 2026-11-16 | الماسترز L0: M_sales_hub (7 أنظمة، 27 اقتباساً) وM_wiki_hub (6 أنظمة، 22 اقتباساً) مع built_from_hash لكل موضوع | python3 tools/gates.py check | 75 كياناً، 0 مرفوض |
