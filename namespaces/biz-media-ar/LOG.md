| Date | What happened | Measured by | Result |
|---|---|---|---|
| 2026-11-16 | إعادة البناء بعد فقد الساندبوكس: 24 مصدر S_ (69,597 كلمة) ثم 19 ذرة T_ (147 اقتباساً) و7 مسارد G_ و4 مفاهيم C_ وتوترين X_ | python3 tools/gates.py check (من داخل namespace) | 49 كيان، 0 مرفوض |
| 2026-11-16 | أسئلة التقييم (14 سؤالاً في 4 طبقات) + قياس BM25 على الـnamespace المُعاد بناؤه | python3 tools/evalrun.py -k 10 (من داخل namespace) | recall@10 = 12/12 = 1.000 (exact 7/7, paraphrase 3/3, comparison 2/2) |
