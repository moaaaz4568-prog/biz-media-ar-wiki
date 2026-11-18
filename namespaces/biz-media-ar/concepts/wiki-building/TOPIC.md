---
type: topic
topic: wiki-building
---

# دليل موضوع بناء الويكي — wiki-building

## مقدمة

يوثّق هذا الموضوع منهجية بناء ويكي المعرفة بالدليل أولاً، كما جمعها الماستر المرجعي [[masters/wiki-building/M_wiki_hub|M_wiki_hub]]. تقوم المنهجية على عمارة طبقية من ثماني طبقات (خام، فمُطبَّع، فمصطلحات، فماسترز، فويكي، ففهرس، ثم تقييم وعمليات) يبقى الخام فيها للقراءة فقط مهما كان السبب، ويُبنى التجميع فوقه ويُعاد بناؤه عند الحاجة؛ فالويكي طبقة تجميع لا طبقة حقيقة، والحقيقة تبقى في الخام. وتحكم النظام قاعدة الدليل أولاً: كل معلومة من مصدر فعلي، وكل سطر معرفي موسوم بواحد من خمسة وسوم (OBSERVED / REPORTED / PROPOSED / UNKNOWN / NOT_RUN)، وكل رقم في تقرير وراءه أمر قياس اشتغل فعلاً وإلا حُذف لا «أُجّل». أما الاسترجاع فيبدأ بالبحث المعجمي BM25 ويُعرَّف نجاحه تشغيلياً بجلب الصفحة الصحيحة وإجابة فيها استشهاد، ويؤجَل التضمين والهجين وreranking وGraphRAG حتى يثبت تفوقاً مقيساً. وتكتمل المنهجية بحوكمة تشغيلية (دورة استكشف ثم خطط ثم نفّذ ثم راجع ثم كرر)، وبنية تحميل تحترم المصدر (سكربت ينام بين الطلبات ويوقف بعد 3 حظرات متتالية، TXT مباشرة لا VTT)، وبداية متدرجة بنموذج صغير — شخصية واحدة وعشرين صفحة عربية — لا يتوسع إلا بقرار بيانات لا قرار حماس. تتجسد هذه المنهجية اليوم في مفهوم واحد جامع مدعوم بخمس ذرات حرفية وخمسة مداخل في المسرد، وهذا الدليل مدخلهما.

## مفاهيم الموضوع (1)

لا تحمل ترويسة هذا المفهوم حقل question:، فالمعتمد في الجدول عنوانه كما ورد في سطر العنوان الأول.

| الملف | العنوان |
| --- | --- |
| [[concepts/wiki-building/C_evidence_first_wiki]] | الويكي بالدليل أولاً |

## الذرات المرتبطة (5)

- [[atoms/wiki-building/T_analysis_prompt_rules]]
- [[atoms/wiki-building/T_conversation_export]]
- [[atoms/wiki-building/T_pro_prompt]]
- [[atoms/wiki-building/T_wiki_talk_decisions_1]]
- [[atoms/wiki-building/T_wiki_talk_decisions_2]]

## المسارد المرتبطة (5)

- [[glossary/wiki-building/G_analysis_prompt]] — برومبت التحليل والاستخراج (Analysis Prompt)
- [[glossary/wiki-building/G_pro_prompt]] — البرومبت الاحترافي (Pro Prompt)
- [[glossary/wiki-building/G_proof_rule]] — قاعدة الدليل (evidence tags: OBSERVED / REPORTED / UNKNOWN)
- [[glossary/wiki-building/G_wiki]] — الويكي (wiki)
- [[glossary/wiki-building/G_yt_wiki]] — yt-wiki

## من أين تبدأ

1. **الأساس المعرفي:** اقرأ الماستر [[masters/wiki-building/M_wiki_hub]] كاملاً، ثم المفهوم الجامع [[concepts/wiki-building/C_evidence_first_wiki]] — منهما تُفهم العمارة الطبقية وقاعدة الوسوم والخام للقراءة فقط.
2. **المصطلحات الحاكمة:** ثم مدخلي المسرد [[glossary/wiki-building/G_wiki]] و[[glossary/wiki-building/G_proof_rule]] لتثبيت تعريف الويكي كطبقة تجميع وقاعدة الوسوم، يليهما [[glossary/wiki-building/G_yt_wiki]] و[[glossary/wiki-building/G_analysis_prompt]] و[[glossary/wiki-building/G_pro_prompt]].
3. **الأدلة الحرفية:** اختم بالذرات الخمس — [[atoms/wiki-building/T_wiki_talk_decisions_1]] و[[atoms/wiki-building/T_wiki_talk_decisions_2]] لقرارات المحادثة، ثم [[atoms/wiki-building/T_conversation_export]] و[[atoms/wiki-building/T_analysis_prompt_rules]] و[[atoms/wiki-building/T_pro_prompt]] — وعُد عند التنفيذ إلى قوالب الماستر (تقرير موسوم، دورة عمل موثقة، فحص ما قبل النشر، توسيع من النموذج الصغير).
