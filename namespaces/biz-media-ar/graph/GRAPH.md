# الجراف العلائقي — biz-media-ar

جراف الكيانات والعلاقات للـnamespace كاملاً، مبني من روابط الـwiki `[[...]]` بين الكيانات
(الوضع RELATIONAL في `forge.py graph`): **89 عقدة، 42 حافة صحيحة، 1 رابط غير محلول**.

## طريقة البناء

1. الأداة الرسمية `python3 tools/forge.py graph --namespace biz-media-ar --json` تمسح كل ملفات الكيانات
   (S_/T_/G_/C_/X_/M_) وتستخرج روابط الـwiki من متن كل ملف.
2. كل رابط يُحل إلى وجهته بالمطابقة على اسم الملف (basename) مع تفضيل نفس الـnamespace.
3. تحقق مستقل: كل عقدة ملف موجود، وكل حافة صحيحة رابطها الخام موجود فعلاً في ملف المرسل — 42/43 حابة تحققت.

## الإحصاءات

| القياس | القيمة |
|---|---|
| العقد | 89 |
| الحواف الصحيحة | 42 |
| الروابط غير المحلولة | 1 |
| العقد بلا أي رابط | 53 |
| عقد atom | 25 |
| عقد concept | 10 |
| عقد glossary | 25 |
| عقد master | 2 |
| عقد source | 24 |
| عقد tension | 3 |
| عقد topic=sales-outbound | 73 |
| عقد topic=wiki-building | 16 |

## أكثر العقد ارتباطاً (درجة ≥ 2)

| العقدة | الدرجة |
|---|---|
| `biz-media-ar/masters/sales-outbound/M_sales_hub.md` | 12 |
| `biz-media-ar/masters/wiki-building/M_wiki_hub.md` | 5 |
| `biz-media-ar/concepts/sales-outbound/C_content_funnel_clarity.md` | 5 |
| `biz-media-ar/concepts/sales-outbound/C_followup_as_system.md` | 5 |
| `biz-media-ar/concepts/sales-outbound/C_diagnose_before_solution.md` | 5 |
| `biz-media-ar/concepts/sales-outbound/C_trust_precedes_transaction.md` | 5 |
| `biz-media-ar/concepts/sales-outbound/C_warmup_throttle.md` | 4 |
| `biz-media-ar/concepts/wiki-building/C_evidence_first_wiki.md` | 3 |
| `biz-media-ar/concepts/sales-outbound/C_one_person_agency.md` | 3 |
| `biz-media-ar/concepts/sales-outbound/C_measure_then_scale.md` | 3 |
| `biz-media-ar/concepts/sales-outbound/C_signal_over_spray.md` | 2 |
| `biz-media-ar/concepts/sales-outbound/C_price_after_value.md` | 2 |
| `biz-media-ar/glossary/wiki-building/G_wiki.md` | 2 |
| `biz-media-ar/glossary/wiki-building/G_proof_rule.md` | 2 |
| `biz-media-ar/tensions/sales-outbound/X_value_vs_infrastructure.md` | 2 |
| `biz-media-ar/tensions/sales-outbound/X_volume_vs_signal.md` | 2 |
| `biz-media-ar/atoms/sales-outbound/T_story_structure.md` | 2 |
| `biz-media-ar/glossary/sales-outbound/G_send_rate_throttle.md` | 2 |

## الروابط غير المحلولة

- `hatch_widget:...` في `biz-media-ar/sources/S_wkt_wiki_all_talk.md` — نص توثيقي داخل backticks (شرح إزالة رموز ويدجت من المصدر عند التنقيح) التقطه المستخرج خطأً؛ ليس رابطاً مكسوراً فعلياً.

## كيف تستخدم الجراف

- استعلام الجيران: `python3 tools/forge.py graph --namespace biz-media-ar --neighbors C_signal_over_spray`
- إعادة البناء بعد أي تغيير: `python3 tools/forge.py graph --namespace biz-media-ar --json` ثم تحديث هذا الملف.
- الجراف يجيب أسئلة «من يرتبط بمن ولماذا»، ولا يستبدل الاسترجاع.

بيانات الجراف الكاملة في `graph/graph.json` بجوار هذا الملف.
