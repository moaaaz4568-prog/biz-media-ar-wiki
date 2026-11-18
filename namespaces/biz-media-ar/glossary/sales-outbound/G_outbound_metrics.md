---
type: glossary
topic: sales-outbound
aka: [مؤشرات البريد البارد, Outbound Metrics]
origin: sources/S_cpt_CPT_CURATED_OUTBOUND_METRICS.md
---

# G_outbound_metrics — مقاييس الإرسال الخارجي (Outbound Metrics)

## المصطلح

مقاييس الإرسال الخارجي في هذا المصدر ليست أسماء مترادفة تُستخدم بالتبادل، بل طبقات قياس منفصلة لا يجوز خلطها في قمع واحد مبهم. التعريف التشغيلي يقوم على تمييز الطبقات: sends وreply rate (نسبة الردود إلى الإرسالات) وpositive reply rate وmeetings booked كطبقات منفصلة، مع أن replies لا تساوي revenue وأن booking/show/close مراحل لاحقة. حدث open (تحميل/فتح) يصفه مصدر Instantly بأنه غير موثوق ويوصي بتجربة تعطيله، وpositive reply رد يبدي اهتمامًا لكنه ليس meeting ولا close. القاعدة العملية: أنشئ قمعًا منفصل الأعمدة، ولا تنقل metric من طبقة إلى أخرى، ولا تعتبر الرد إيرادًا.

## المرادفات

- Outbound Metrics (الاسم الإنجليزي)
- طبقات قياس البريد البارد / قمع الإرسال الخارجي (وصف وظيفي وفق المصدر)

## المثال الحي

> "المصدر يعرّف sends وreply rate وpositive reply rate وmeetings booked كطبقات منفصلة (**CLM_CURATED_OUTBOUND_METRICS_001**)، بينما يوضح Smartlead أن replies لا تساوي revenue وأن booking/show/close مراحل لاحقة (**CLM_CURATED_OUTBOUND_METRICS_003**)." — sources/S_cpt_CPT_CURATED_OUTBOUND_METRICS.md

## متى ينكسر المعنى

- حين تُستخدم الطبقات كأسماء مترادفة أو يُنقل metric من طبقة إلى أخرى: المصدر يرفض ذلك صراحة، فالتركيز على open قد يعطي صورة زائفة لكونه حدثًا غير موثوق.
- حين يُقرأ الرد كإيراد أو نتيجة نهائية: الرد — حتى الpositive reply الذي يبدي اهتمامًا — ليس meeting ولا close، والتركيز عليه قد يخفي فشل الحجز أو الحضور أو الإغلاق.
