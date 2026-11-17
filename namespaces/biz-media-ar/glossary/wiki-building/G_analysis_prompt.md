---
type: glossary
topic: wiki-building
aka: [برومبت التحليل والاستخراج, Analysis Prompt, برومبت المونتاج]
origin: sources/S_wkt_prompt.md
---

# G_analysis_prompt — برومبت التحليل والاستخراج (Analysis Prompt)

## المصطلح

برومبت التحليل والاستخراج هو برومبت تشغيلي لمحرر فيديو أول + مدير موشن جرافيك يعمل ذاتياً داخل Google Antigravity، مهمته تحويل المدخل الخام (فيديو متحدث، تسجيل شاشة، أو صوت فقط) إلى فيديو جاهز للنشر عالي الاحتفاظ. قواعده غير القابلة للتفاوض هي هويته: لا اختلاق وقائع أو أرقام أو أسماء (كل كلمة على الشاشة من الترانسكربت)، الرسومات تشرح لا تزيّن، والعربية مقدسة (RTL دائماً، لا أنيميشن حرفاً-بحرف، لا letter-spacing، والعزل LTR للمصطلحات الإنجليزية). المرجعية الكاملة للألوان والخطوط والتوقيتات تأتي من tokens في MOTION.md — لا قيم ارتجالية.

## المرادفات

- Analysis Prompt (الاسم الإنجليزي)
- برومبت المونتاج والاستخراج (وصف وظيفي)

## المثال الحي

> "Never invent facts, numbers, names, prices or claims. Every on-screen word comes from my transcript (shortened is fine, changed meaning is not)." — sources/S_wkt_prompt.md
> "Graphics must EXPLAIN what I say (steps, comparisons, numbers, UI, flows). Decoration without meaning is a failure." — sources/S_wkt_prompt.md
> "Arabic is sacred: always RTL; never animate Arabic letter by letter (animate per word or per line); never add letter-spacing to Arabic; isolate English terms as LTR" — sources/S_wkt_prompt.md

## متى ينكسر المعنى

- حين تُختزل القواعد في الجودة البصرية: جوهر البرومبت النزاهة المعرفية (لا اختلاق) قبل الإخراج — اختصار الكلمة مسموح وتغيير المعنى ليس كذلك.
- حين تُقرأ القواعد قائمة أمنيات: البرومبت يفرض بوابات (QA في Phase 8، وسؤال واحد مسموح عن الصوت فقط) والعمل صامت ذاتي — Work silently and autonomously.
- حين تُتجاهل المرجعية الموحدة: الخروج عن tokens في MOTION.md بأي قيمة ad-hoc خرقٌ صريح للتعريف لا اجتهاداً.
