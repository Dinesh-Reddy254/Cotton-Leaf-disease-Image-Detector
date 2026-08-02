/* ═══════════════════════════════════════════════════════════════
   CottonGreen AI — Multilingual Translations (EN / TE / HI)
   ═══════════════════════════════════════════════════════════════ */

window.TRANSLATIONS = {

  // ─────────────────────────────────────────────────────────────
  // ENGLISH
  // ─────────────────────────────────────────────────────────────
  en: {
    nav_diagnose: "Diagnose",
    nav_diseases: "Diseases",
    nav_history: "History",
    nav_about: "About",
    model_ready: "Model Ready",
    model_not_loaded: "No Model",

    // Hero
    hero_tag: "🤖 Deep Learning · EfficientNetB3",
    hero_title_1: "AI-Powered Cotton Leaf",
    hero_title_2: "Diseases Detection",
    hero_sub: "Upload a cotton leaf photo to receive an AI-powered disease diagnosis with confidence scores and treatment recommendations.",
    stat_classes: "Disease Classes",
    stat_accuracy: "Test Accuracy",
    stat_realtime: "Real-time",
    stat_prediction: "Prediction",
    hero_card_label: "AI Analysis",

    // Upload Section
    upload_title: "Upload Leaf Image",
    upload_subtitle: "Drag & drop or click to select a cotton leaf photo (JPG, PNG, WebP)",
    drop_text_strong: "Drag & drop your image here",
    drop_text_span: "or click to browse files",
    drop_hint: "Supports JPG · PNG · WebP · Max 16MB",
    tip_1: "📸 Use clear, well-lit images",
    tip_2: "🍃 Ensure leaf fills most of the frame",
    tip_3: "🔍 Avoid blurry or dark photos",
    tip_4: "📱 Phone camera works perfectly",
    idle_text: "Select a cotton leaf image to begin AI analysis",
    ready_text: "Image ready for analysis",
    btn_start: "Start Diagnosis →",
    btn_analyze: "Analyze Leaf",
    btn_analyzing: "Analyzing...",
    btn_new: "New Diagnosis",
    btn_print: "Print Report",
    btn_retry: "Try Again",
    err_title: "Diagnosis Failed",
    
    // Result
    res_title: "Diagnosis Complete",
    res_conf: "CONFIDENCE",
    res_desc: "DESCRIPTION",
    res_cause: "CAUSE",
    res_treat: "TREATMENT & REMEDIES",
    res_other: "OTHER POSSIBILITIES",

    // History
    hist_title: "Recent Diagnoses",
    hist_empty: "No diagnoses yet. Upload an image to see your history here.",
    
    // About
    about_title: "About CottonGreen AI",
    about_p1: "CottonGreen AI is built to help farmers rapidly identify cotton leaf diseases. By combining deep learning with a simple web interface, we aim to reduce crop loss and promote sustainable farming practices.",
    about_p2: "This project uses an EfficientNetB3 model trained on thousands of labeled cotton leaves.",

    // Footer
    foot_made: "Made for Cotton Farmers everywhere.",
    
    // Dynamic JS
    model_loading: "Waking up model...",
    error_network: "Network error. Please try again.",
    error_upload: "Failed to process image.",

    diseases: {
      "Aphids": {
        name: "Aphids",
        desc: "Small sap-sucking insects that cause leaves to curl and turn yellow.",
        cause: "Infestation by aphids (Aphis gossypii), often exacerbated by dry, warm weather.",
        treatment: "Use neem oil or insecticidal soap. Introduce ladybugs. For severe cases, use Imidacloprid."
      },
      "Army worm": {
        name: "Army Worm",
        desc: "Caterpillars that consume leaf tissue, leaving skeletonized foliage.",
        cause: "Larvae of the Spodoptera frugiperda moth laying eggs on cotton leaves.",
        treatment: "Apply Bacillus thuringiensis (Bt) or Spinosad. Remove heavily infested leaves."
      },
      "Bacterial Blight": {
        name: "Bacterial Blight",
        desc: "Dark, water-soaked angular spots on leaves that turn black.",
        cause: "Xanthomonas citri bacteria spreading via rain splash or infected seeds.",
        treatment: "Apply copper-based fungicides. Ensure good field drainage. Plant resistant varieties."
      },
      "Healthy": {
        name: "Healthy Cotton",
        desc: "No visible signs of disease or pest infestation.",
        cause: "Optimal growing conditions and good crop management.",
        treatment: "Maintain current irrigation and nutrient schedule."
      },
      "Leaf Redding": {
        name: "Leaf Redding",
        desc: "Leaves turn red/purple starting from the margins.",
        cause: "Magnesium/Nitrogen deficiency, water stress, or sudden temperature drops.",
        treatment: "Apply Magnesium Sulfate (Epsom salt) foliar spray. Ensure consistent watering."
      },
      "Powdery Mildew": {
        name: "Powdery Mildew",
        desc: "White, powdery fungal growth on the upper and lower leaf surfaces.",
        cause: "Ramularia areola fungus thriving in high humidity and warm temperatures.",
        treatment: "Apply sulfur-based fungicides or appropriate triazole sprays. Improve air circulation."
      },
      "Target Spot": {
        name: "Target Spot",
        desc: "Concentric circular lesions resembling a target board, causing premature defoliation.",
        cause: "Corynespora cassiicola fungus favored by extended periods of leaf wetness.",
        treatment: "Apply protective fungicides like Pyraclostrobin before canopy closure."
      },
      "Not a Cotton Leaf": {
        name: "Not a Cotton Leaf",
        desc: "This image does not appear to be a plant or cotton leaf.",
        cause: "Our AI detected that this image is out of distribution.",
        treatment: "Please upload a clear picture of a cotton leaf."
      }
    }
  },

  // ─────────────────────────────────────────────────────────────
  // TELUGU
  // ─────────────────────────────────────────────────────────────
  te: {
    nav_diagnose: "వ్యాధి నిర్ధారణ",
    nav_diseases: "వ్యాధులు",
    nav_history: "చరిత్ర",
    nav_about: "గురించి",
    model_ready: "సిద్ధంగా ఉంది",
    model_not_loaded: "సిద్ధంగా లేదు",

    hero_tag: "🤖 డీప్ లెర్నింగ్ · EfficientNetB3",
    hero_title_1: "AI-ఆధారిత పత్తి ఆకు",
    hero_title_2: "వ్యాధి గుర్తింపు",
    hero_sub: "AI-ఆధారిత వ్యాధి నిర్ధారణ మరియు చికిత్స సిఫార్సులను పొందడానికి పత్తి ఆకు ఫోటోను అప్‌లోడ్ చేయండి.",
    stat_classes: "వ్యాధి రకాలు",
    stat_accuracy: "ఖచ్చితత్వం",
    stat_realtime: "తక్షణ",
    stat_prediction: "ఫలితం",
    hero_card_label: "AI విశ్లేషణ",

    upload_title: "ఆకు చిత్రాన్ని అప్‌లోడ్ చేయండి",
    upload_subtitle: "పత్తి ఆకు ఫోటోను ఎంచుకోవడానికి ఇక్కడ క్లిక్ చేయండి",
    drop_text_strong: "చిత్రాన్ని ఇక్కడ లాగి వదలండి",
    drop_text_span: "లేదా ఫైళ్లను బ్రౌజ్ చేయడానికి క్లిక్ చేయండి",
    drop_hint: "JPG · PNG · WebP · Max 16MB",
    tip_1: "📸 స్పష్టమైన, మంచి కాంతి ఉన్న చిత్రాలను ఉపయోగించండి",
    tip_2: "🍃 ఆకు ఫ్రేమ్ మొత్తాన్ని నింపేలా చూసుకోండి",
    tip_3: "🔍 అస్పష్టంగా ఉన్న ఫోటోలను నివారించండి",
    tip_4: "📱 ఫోన్ కెమెరా అద్భుతంగా పనిచేస్తుంది",
    idle_text: "AI విశ్లేషణ ప్రారంభించడానికి పత్తి ఆకు చిత్రాన్ని ఎంచుకోండి",
    ready_text: "విశ్లేషణకు చిత్రం సిద్ధంగా ఉంది",
    btn_start: "నిర్ధారణ ప్రారంభించండి →",
    btn_analyze: "ఆకును విశ్లేషించండి",
    btn_analyzing: "విశ్లేషిస్తోంది...",
    btn_new: "కొత్త నిర్ధారణ",
    btn_print: "రిపోర్ట్ ప్రింట్ చేయండి",
    btn_retry: "మళ్ళీ ప్రయత్నించండి",
    err_title: "నిర్ధారణ విఫలమైంది",
    
    res_title: "నిర్ధారణ పూర్తయింది",
    res_conf: "ఖచ్చితత్వం (CONFIDENCE)",
    res_desc: "వివరణ",
    res_cause: "కారణం",
    res_treat: "చికిత్స & నివారణ చర్యలు",
    res_other: "ఇతర అవకాశాలు",

    hist_title: "ఇటీవలి నిర్ధారణలు",
    hist_empty: "ఇంకా నిర్ధారణలు లేవు. మీ చరిత్రను చూడటానికి చిత్రాన్ని అప్‌లోడ్ చేయండి.",
    
    about_title: "CottonGreen AI గురించి",
    about_p1: "రైతులకు పత్తి ఆకు వ్యాధులను త్వరగా గుర్తించడంలో సహాయపడటానికి CottonGreen AI నిర్మించబడింది.",
    about_p2: "ఈ ప్రాజెక్ట్ వేలాది పత్తి ఆకులపై శిక్షణ పొందిన మోడల్‌ను ఉపయోగిస్తుంది.",
    foot_made: "ప్రపంచవ్యాప్తంగా ఉన్న పత్తి రైతుల కోసం రూపొందించబడింది.",
    
    model_loading: "మోడల్ లోడ్ అవుతోంది...",
    error_network: "నెట్‌వర్క్ లోపం. దయచేసి మళ్లీ ప్రయత్నించండి.",
    error_upload: "చిత్రాన్ని ప్రాసెస్ చేయడం విఫలమైంది.",

    diseases: {
      "Aphids": {
        name: "పేనుబంక (Aphids)",
        desc: "చిన్న పురుగులు ఆకు రసాన్ని పీల్చడం వల్ల ఆకులు ముడతలు పడి పసుపు రంగులోకి మారుతాయి.",
        cause: "పొడి మరియు వెచ్చని వాతావరణం వల్ల అఫిడ్స్ ఉధృతి పెరుగుతుంది.",
        treatment: "వేప నూనె వాడండి. తీవ్రంగా ఉంటే ఇమిడాక్లోప్రిడ్ పిచికారీ చేయండి."
      },
      "Army worm": {
        name: "లద్దెపురుగు (Army Worm)",
        desc: "గొంగళి పురుగులు ఆకు కణజాలాన్ని తిని ఆకులను అస్థిపంజరంగా మారుస్తాయి.",
        cause: "స్పోడోప్టెరా మోత్ పత్తి ఆకులపై గుడ్లు పెట్టడం వల్ల.",
        treatment: "బాసిల్లస్ తురింజియెన్సిస్ (Bt) లేదా స్పినోసాడ్ వాడండి."
      },
      "Bacterial Blight": {
        name: "బాక్టీరియల్ బ్లైట్ (Bacterial Blight)",
        desc: "ఆకులపై నల్లటి నీటి మచ్చలు ఏర్పడతాయి.",
        cause: "వర్షపు చినుకుల ద్వారా లేదా వ్యాధిగ్రస్తులైన విత్తనాల ద్వారా వ్యాపిస్తుంది.",
        treatment: "రాగి ఆధారిత శిలీంద్రనాశకాలను పిచికారీ చేయండి."
      },
      "Healthy": {
        name: "ఆరోగ్యకరమైన పత్తి (Healthy)",
        desc: "వ్యాధి లేదా చీడపీడల సంకేతాలు లేవు.",
        cause: "మంచి పంట నిర్వహణ.",
        treatment: "ప్రస్తుత నీటి పారుదల మరియు పోషకాల షెడ్యూల్‌ను కొనసాగించండి."
      },
      "Leaf Redding": {
        name: "ఆకు ఎర్రబడటం (Leaf Redding)",
        desc: "ఆకులు అంచుల నుండి ఎరుపు/ఊదా రంగులోకి మారుతాయి.",
        cause: "మెగ్నీషియం లోపం లేదా నీటి ఒత్తిడి.",
        treatment: "మెగ్నీషియం సల్ఫేట్ ఫ్లోలియర్ స్ప్రే చేయండి."
      },
      "Powdery Mildew": {
        name: "బూజు తెగులు (Powdery Mildew)",
        desc: "ఆకులపై తెల్లని బూజు లాంటి శిలీంధ్రాల పెరుగుదల.",
        cause: "అధిక తేమ మరియు వెచ్చని ఉష్ణోగ్రతలు.",
        treatment: "గంధకం ఆధారిత శిలీంద్రనాశకాలను పిచికారీ చేయండి."
      },
      "Target Spot": {
        name: "టార్గెట్ స్పాట్ (Target Spot)",
        desc: "ఆకులపై వలయాకారపు మచ్చలు ఏర్పడి ఆకులు రాలిపోతాయి.",
        cause: "ఆకులు ఎక్కువసేపు తడిచి ఉండటం వల్ల.",
        treatment: "పైరాక్లోస్ట్రోబిన్ వంటి శిలీంద్రనాశకాలను వాడండి."
      },
      "Not a Cotton Leaf": {
        name: "పత్తి ఆకు కాదు",
        desc: "ఈ చిత్రం మొక్క లేదా పత్తి ఆకు లాగా కనిపించడం లేదు.",
        cause: "మా AI ఈ చిత్రం తప్పుగా ఉన్నట్లు గుర్తించింది.",
        treatment: "దయచేసి పత్తి ఆకు యొక్క స్పష్టమైన చిత్రాన్ని అప్‌లోడ్ చేయండి."
      }
    }
  },

  // ─────────────────────────────────────────────────────────────
  // HINDI
  // ─────────────────────────────────────────────────────────────
  hi: {
    nav_diagnose: "निदान",
    nav_diseases: "बीमारियां",
    nav_history: "इतिहास",
    nav_about: "हमारे बारे में",
    model_ready: "मॉडल तैयार",
    model_not_loaded: "मॉडल नहीं है",

    hero_tag: "🤖 डीप लर्निंग · EfficientNetB3",
    hero_title_1: "AI-संचालित कपास की पत्ती",
    hero_title_2: "रोग की पहचान",
    hero_sub: "AI-संचालित रोग निदान और उपचार सिफ़ारिशें प्राप्त करने के लिए कपास की पत्ती की तस्वीर अपलोड करें।",
    stat_classes: "रोग श्रेणियाँ",
    stat_accuracy: "सटीकता",
    stat_realtime: "वास्तविक समय",
    stat_prediction: "अनुमान",
    hero_card_label: "AI विश्लेषण",

    upload_title: "पत्ती की छवि अपलोड करें",
    upload_subtitle: "कपास की पत्ती की तस्वीर चुनने के लिए क्लिक करें",
    drop_text_strong: "अपनी छवि को यहाँ खींचें और छोड़ें",
    drop_text_span: "या फ़ाइलें ब्राउज़ करने के लिए क्लिक करें",
    drop_hint: "समर्थित: JPG · PNG · WebP · Max 16MB",
    tip_1: "📸 स्पष्ट, अच्छी रोशनी वाली छवियों का उपयोग करें",
    tip_2: "🍃 सुनिश्चित करें कि पत्ती पूरी स्क्रीन पर हो",
    tip_3: "🔍 धुंधली तस्वीरों से बचें",
    tip_4: "📱 फोन का कैमरा भी ठीक से काम करता है",
    idle_text: "AI विश्लेषण शुरू करने के लिए कपास की पत्ती की छवि चुनें",
    ready_text: "छवि विश्लेषण के लिए तैयार है",
    btn_start: "निदान शुरू करें →",
    btn_analyze: "पत्ती का विश्लेषण करें",
    btn_analyzing: "विश्लेषण हो रहा है...",
    btn_new: "नया निदान",
    btn_print: "रिपोर्ट प्रिंट करें",
    btn_retry: "पुनः प्रयास करें",
    err_title: "निदान विफल रहा",
    
    res_title: "निदान पूर्ण",
    res_conf: "आत्मविश्वास (CONFIDENCE)",
    res_desc: "विवरण",
    res_cause: "कारण",
    res_treat: "उपचार एवं उपाय",
    res_other: "अन्य संभावनाएं",

    hist_title: "हाल के निदान",
    hist_empty: "अभी तक कोई निदान नहीं। अपना इतिहास देखने के लिए एक छवि अपलोड करें।",
    
    about_title: "CottonGreen AI के बारे में",
    about_p1: "CottonGreen AI किसानों को कपास की पत्ती की बीमारियों को जल्दी पहचानने में मदद करने के लिए बनाया गया है।",
    about_p2: "यह प्रोजेक्ट हजारों कपास के पत्तों पर प्रशिक्षित मॉडल का उपयोग करता है।",
    foot_made: "सभी जगह कपास किसानों के लिए बनाया गया।",
    
    model_loading: "मॉडल लोड हो रहा है...",
    error_network: "नेटवर्क त्रुटि। कृपया पुनः प्रयास करें।",
    error_upload: "छवि को प्रोसेस करने में विफल।",

    diseases: {
      "Aphids": {
        name: "माहू (Aphids)",
        desc: "छोटे रस चूसने वाले कीड़े जिसके कारण पत्तियां मुड़कर पीली पड़ जाती हैं।",
        cause: "शुष्क, गर्म मौसम में एफिड्स का प्रकोप बढ़ जाता है।",
        treatment: "नीम के तेल का प्रयोग करें। गंभीर होने पर इमिडाक्लोप्रिड का प्रयोग करें।"
      },
      "Army worm": {
        name: "सैनिक कीट (Army Worm)",
        desc: "कैटरपिलर जो पत्ती को खाते हैं, जिससे केवल कंकाल बचता है।",
        cause: "कपास के पत्तों पर अंडे देने वाला स्पोडोप्टेरा कीट।",
        treatment: "बैसिलस थुरिंजिएंसिस (Bt) या स्पिनोसैड लागू करें।"
      },
      "Bacterial Blight": {
        name: "बैक्टीरियल ब्लाइट (Bacterial Blight)",
        desc: "पत्तियों पर काले पानी से लथपथ कोणीय धब्बे।",
        cause: "बारिश के छींटों या संक्रमित बीजों के माध्यम से फैलने वाला बैक्टीरिया।",
        treatment: "तांबे आधारित कवकनाशी (Fungicides) लागू करें।"
      },
      "Healthy": {
        name: "स्वस्थ कपास (Healthy)",
        desc: "रोग या कीट के संक्रमण का कोई दिखाई देने वाला संकेत नहीं।",
        cause: "अच्छी फसल प्रबंधन।",
        treatment: "वर्तमान सिंचाई और पोषक तत्वों का शेड्यूल बनाए रखें।"
      },
      "Leaf Redding": {
        name: "पत्ती का लाल होना (Leaf Redding)",
        desc: "पत्तियाँ किनारों से शुरू होकर लाल/बैंगनी रंग की हो जाती हैं।",
        cause: "मैग्नीशियम की कमी या पानी का तनाव।",
        treatment: "मैग्नीशियम सल्फेट फोलियर स्प्रे लागू करें।"
      },
      "Powdery Mildew": {
        name: "पाउडरी मिल्ड्यू (Powdery Mildew)",
        desc: "पत्ती की ऊपरी और निचली सतहों पर सफेद पाउडर जैसा फंगल विकास।",
        cause: "उच्च आर्द्रता और गर्म तापमान में कवक का पनपना।",
        treatment: "सल्फर आधारित कवकनाशी लागू करें।"
      },
      "Target Spot": {
        name: "टारगेट स्पॉट (Target Spot)",
        desc: "पत्तियों पर गोलाकार धब्बे, जिससे पत्तियां समय से पहले गिर जाती हैं।",
        cause: "पत्ती के लंबे समय तक गीले रहने के कारण।",
        treatment: "पाइराक्लोस्ट्रोबिन (Pyraclostrobin) जैसे कवकनाशी लागू करें।"
      },
      "Not a Cotton Leaf": {
        name: "कपास की पत्ती नहीं है",
        desc: "यह छवि किसी पौधे या कपास के पत्ते की प्रतीत नहीं होती है।",
        cause: "हमारे AI ने पता लगाया कि यह छवि सही नहीं है।",
        treatment: "कृपया कपास के पत्ते की एक स्पष्ट तस्वीर अपलोड करें।"
      }
    }
  }

};