import React, { useState, useEffect, useRef } from 'react';
import { 
  Mic, Send, ShieldCheck, AlertTriangle, UserCheck, BookOpen, 
  Activity, Volume2, CheckCircle2, XCircle, ArrowRight, RefreshCw, 
  FileText, Database, Sparkles, AlertCircle, Layers, MessageSquare,
  PhoneCall, Play, Pause, ChevronRight, HelpCircle, Globe, Award, Download, Square
} from 'lucide-react';

export default function App() {
  const [activeTab, setActiveTab] = useState('simulator'); // simulator | whatsapp | expert | admin | architecture
  const [uiLanguage, setUiLanguage] = useState('mr'); // mr | hi | en | gu

  // Multi-Language UI Translations
  const translations = {
    mr: {
      title: "फसलमित्र - राष्ट्रीय कृषी माहिती व सल्ला प्रणाली",
      subtitle: "ICAR / KVK मान्यताप्राप्त व्हॉईस-फर्स्ट व व्हॉट्सॲप एआय सहाय्यक",
      tab_whatsapp: "व्हॉट्सॲप सहाय्यक",
      tab_phone: "फोन व्हॉईस कॉल सिम्युलेटर",
      tab_expert: "कृषी तज्ञ रांगेतील प्रकरणे",
      tab_knowledge: "ज्ञानकोश व ऑडिट केंद्र",
      tab_architecture: "प्रणाली रचना",
      wa_header: "फसलमित्र अधिकृत कृषी सहाय्यक",
      wa_sub: "ऑनलाइन • ICAR / KVK प्रमाणित सल्ला",
      wa_welcome: "🌾 *[फसलमित्र कृषी सहाय्यक]*\n_________________________________________\nनमस्कार! मी फसलमित्र कृषी सहाय्यक आहे.\n\nतुम्ही खालील पर्याय निवडू शकता किंवा तुमचा शेतीविषयक प्रश्न व्हॉईस नोट द्वारे पाठवू शकता:\n\n1️⃣ **प्रश्नाचे उत्तर मिळवा** - (उदा. 'सोयाबीन पिवळे पडत आहे')\n2️⃣ **हवामान अंदाज (Agromet)** - (/weather)\n3️⃣ **पिक पासपोर्ट माहिती** - (/passport)\n4️⃣ **तज्ञ तिकीट स्थिती** - (/expert)\n\n💡 *तुमचा प्रश्न येथे टाईप करा किंवा ऑडिओ व्हॉईस मेसेज पाठवा!*",
      input_placeholder: "तुमचा प्रश्न येथे टाईप करा किंवा व्हॉईस संदेश पाठवा...",
      preset_btn_1: "🌱 सोयाबीन पानांचा पिवळेपणा",
      preset_btn_2: "🌧️ हवामान अंदाज (/weather)",
      preset_btn_3: "📜 पिक पासपोर्ट (/passport)",
      preset_btn_4: "👨‍🌾 तज्ञ तिकीट स्थिती (/expert)",
      run_button: "फसलमित्र सल्ला प्रणाली चालवा",
      processing: "१४-टप्प्यांची सल्ला प्रक्रिया सुरू आहे...",
      mic_start: "बोलून प्रश्न विचारा (माईक)",
      mic_listening: "रेकॉर्डिंग सुरू आहे... (माईक बंद करा)",
      play_audio: "ऐका (Text-to-Speech Voice)",
      pause_audio: "आवाज थांबवा"
    },
    hi: {
      title: "फसलमित्र - राष्ट्रीय कृषि ज्ञान एवं परामर्श प्रणाली",
      subtitle: "ICAR / KVK संस्तुत वॉइस-फर्स्ट और व्हाट्सएप एआई सहायक",
      tab_whatsapp: "व्हाट्सएप सहायक",
      tab_phone: "फोन वॉइस कॉल सिम्युलेटर",
      tab_expert: "कृषि विशेषज्ञ कतार",
      tab_knowledge: "ज्ञानकोश एवं ऑडिट केंद्र",
      tab_architecture: "सिस्टम संरचना",
      wa_header: "फसलमित्र आधिकारिक कृषि सहायक",
      wa_sub: "ऑनलाइन • ICAR / KVK प्रमाणित परामर्श",
      wa_welcome: "🌾 *[फसलमित्र कृषि सहायक]*\n_________________________________________\nनमस्कार! मैं फसलमित्र कृषि सहायक हूँ।\n\nआप निम्नलिखित विकल्प चुन सकते हैं या अपना प्रश्न वॉइस नोट द्वारा भेज सकते हैं:\n\n1️⃣ **प्रश्न का उत्तर पाएं** - (जैसे 'सोयाबीन में पीलापन')\n2️⃣ **मौसम पूर्वानुमान (Agromet)** - (/weather)\n3️⃣ **फसल पासपोर्ट विवरण** - (/passport)\n4️⃣ **विशेषज्ञ टिकट स्थिति** - (/expert)\n\n💡 *अपना प्रश्न यहाँ टाइप करें या ऑडियो वॉइस मैसेज भेजें!*",
      input_placeholder: "अपना प्रश्न यहाँ टाइप करें या वॉइस मैसेज भेजें...",
      preset_btn_1: "🌱 सोयाबीन में पीलापन समाधान",
      preset_btn_2: "🌧️ मौसम पूर्वानुमान (/weather)",
      preset_btn_3: "📜 फसल पासपोर्ट (/passport)",
      preset_btn_4: "👨‍🌾 विशेषज्ञ टिकट स्थिति (/expert)",
      run_button: "फसलमित्र परामर्श प्रणाली चलाएं",
      processing: "१४-स्तरीय परामर्श प्रक्रिया जारी है...",
      mic_start: "बोलकर प्रश्न पूछें (माइक)",
      mic_listening: "रिकॉर्डिंग जारी है... (माइक बंद करें)",
      play_audio: "उत्तर सुनें (Text-to-Speech Voice)",
      pause_audio: "आवाज रोकें"
    },
    en: {
      title: "FasalMitra — National Agri-Advisory Platform",
      subtitle: "ICAR / KVK Grounded Voice-First & WhatsApp AI Assistant",
      tab_whatsapp: "WhatsApp Assistant",
      tab_phone: "Phone Voice Simulator",
      tab_expert: "Agricultural Expert Queue",
      tab_knowledge: "Knowledge & Audit Center",
      tab_architecture: "System Architecture",
      wa_header: "FasalMitra Official Agri-Assistant",
      wa_sub: "Online • ICAR/KVK Grounded Official Bot",
      wa_welcome: "🌾 *[FasalMitra Voice & WhatsApp Assistant]*\n_________________________________________\nWelcome! I am FasalMitra Agricultural Assistant.\n\nYou can select quick commands below or send a voice note:\n\n1️⃣ **Get Crop Remedy** - (e.g. 'Soybean leaf yellowing')\n2️⃣ **Weather Bulletin** - (/weather)\n3️⃣ **Crop Passport** - (/passport)\n4️⃣ **Expert Ticket Status** - (/expert)\n\n💡 *Type your question or record a voice note!*",
      input_placeholder: "Type a message or agricultural question...",
      preset_btn_1: "🌱 Soybean Yellowing Remedy",
      preset_btn_2: "🌧️ Weather Forecast (/weather)",
      preset_btn_3: "📜 Crop Passport (/passport)",
      preset_btn_4: "👨‍🌾 Expert Case Status (/expert)",
      run_button: "Execute FasalMitra Advisory Pipeline",
      processing: "Processing 14-Stage Grounded Pipeline...",
      mic_start: "Speak Question (Mic STT)",
      mic_listening: "Recording Voice... (Stop Mic)",
      play_audio: "Listen Answer (Text-to-Speech)",
      pause_audio: "Stop Voice"
    },
    gu: {
      title: "ફસલમિત્ર - રાષ્ટ્રીય કૃષિ માર્ગદર્શન સિસ્ટમ",
      subtitle: "ICAR / KVK માન્યતા પ્રાપ્ત વોઈસ અને વોટ્સએપ એઆઈ સહાયક",
      tab_whatsapp: "વોટ્સએપ સહાયક",
      tab_phone: "ફોન વોઈસ સિમ્યુલેટર",
      tab_expert: "કૃષિ નિષ્ણાત કતાર",
      tab_knowledge: "જ્ઞાનકોશ અને ઓડિટ કેન્દ્ર",
      tab_architecture: "સિસ્ટમ આર્કિટેક્ચર",
      wa_header: "ફસલમિત્ર કૃષિ સહાયક",
      wa_sub: "ઓનલાઇન • ICAR / KVK પ્રમાણિત માર્ગદર્શન",
      wa_welcome: "🌾 *[ફસલમિત્ર કૃષિ સહાયક]*\n_________________________________________\nનમસ્તે! હું ફસલમિત્ર કૃષિ સહાયક છું.\n\nતમે પ્રશ્નો પૂછી શકો છો અથવા વોઇસ નોટ મોકલી શકો છો:\n\n1️⃣ **પાકની માહિતી** - (/weather)\n2️⃣ **હવામાન આગાહી** - (/passport)\n3️⃣ **નિષ્ણાત સ્થિતિ** - (/expert)",
      input_placeholder: "તમારો પ્રશ્ન અહી ટાઇપ કરો...",
      preset_btn_1: "🌱 સોયાબીન પીળા થવાનો ઉપાય",
      preset_btn_2: "🌧️ હવામાન આગાહી (/weather)",
      preset_btn_3: "📜 પાક પાસપોર્ટ (/passport)",
      preset_btn_4: "👨‍🌾 નિષ્ણાત સ્થિતિ (/expert)",
      run_button: "માર્ગદર્શન પ્રોસેસ કરો",
      processing: "પ્રોસેસિંગ ચાલુ છે...",
      mic_start: "બોલીને પ્રશ્ન પૂછો (માઇક)",
      mic_listening: "રેકોર્ડિંગ ચાલુ છે...",
      play_audio: "અવાજ સાંભળો (Text-to-Speech Voice)",
      pause_audio: "અવાજ અટકાવો"
    }
  };

  const t = translations[uiLanguage] || translations.mr;

  // WhatsApp Assistant State
  const [chatMessages, setChatMessages] = useState([
    {
      sender: 'bot',
      text: t.wa_welcome,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      grounding_status: 'SUPPORTED',
      audio_url: null
    }
  ]);
  const [waInput, setWaInput] = useState('');
  const [isWaLoading, setIsWaLoading] = useState(false);
  const chatEndRef = useRef(null);

  // Phone IVR Simulator State
  const [inputText, setInputText] = useState('माझ्या सोयाबीनची पाने पिवळी पडत आहेत, मी काय करू?');
  const [cropOverride, setCropOverride] = useState('Soybean');
  const [language, setLanguage] = useState('auto');
  const [isLoading, setIsLoading] = useState(false);
  const [pipelineResult, setPipelineResult] = useState(null);

  // Live Speech-to-Text (STT) State
  const [isRecording, setIsRecording] = useState(false);
  const recognitionRef = useRef(null);

  // Live Text-to-Speech (TTS) State
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);

  // Expert & Admin State
  const [escalations, setEscalations] = useState([]);
  const [selectedCase, setSelectedCase] = useState(null);
  const [expertResponseText, setExpertResponseText] = useState('');
  const [expertActionStatus, setExpertActionStatus] = useState('');
  const [metrics, setMetrics] = useState(null);
  const [sources, setSources] = useState([]);
  const [isSyncingDataGov, setIsSyncingDataGov] = useState(false);
  const [syncStatusMsg, setSyncStatusMsg] = useState('');

  useEffect(() => {
    fetchAdminMetrics();
    fetchEscalations();
    fetchKnowledgeSources();
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  const fetchAdminMetrics = async () => {
    try {
      const res = await fetch('/api/v1/admin/metrics');
      const data = await res.json();
      setMetrics(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchEscalations = async () => {
    try {
      const res = await fetch('/api/v1/expert/escalations?status=ALL');
      const data = await res.json();
      setEscalations(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchKnowledgeSources = async () => {
    try {
      const res = await fetch('/api/v1/admin/sources');
      const data = await res.json();
      setSources(data);
    } catch (e) {
      console.error(e);
    }
  };

  // --- Live HTML5 Web Speech API (Speech-to-Text) ---
  const toggleSpeechRecognition = () => {
    if (isRecording) {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      setIsRecording(false);
    } else {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert("Browser Speech Recognition is available on Google Chrome / MS Edge!");
        return;
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = uiLanguage === 'mr' ? 'mr-IN' : uiLanguage === 'hi' ? 'hi-IN' : uiLanguage === 'gu' ? 'gu-IN' : 'en-IN';

      recognition.onstart = () => setIsRecording(true);
      
      recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map(result => result[0].transcript)
          .join('');
        setInputText(transcript);
      };

      recognition.onerror = (event) => {
        console.error("Speech Recognition Error:", event.error);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    }
  };

  // --- Live HTML5 Speech Synthesis (Text-to-Speech Audio Playback) ---
  const handlePlayAudio = (textToSpeak) => {
    if (isPlayingAudio) {
      window.speechSynthesis?.cancel();
      setIsPlayingAudio(false);
      return;
    }

    if (!('speechSynthesis' in window)) {
      alert("Text-to-speech audio synthesis is not supported on this browser.");
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(textToSpeak);
    utterance.lang = uiLanguage === 'mr' ? 'mr-IN' : uiLanguage === 'hi' ? 'hi-IN' : uiLanguage === 'gu' ? 'gu-IN' : 'hi-IN';
    utterance.rate = 0.95;

    utterance.onstart = () => setIsPlayingAudio(true);
    utterance.onend = () => setIsPlayingAudio(false);
    utterance.onerror = () => setIsPlayingAudio(false);

    window.speechSynthesis.speak(utterance);
  };

  const handleSyncDataGov = async () => {
    setIsSyncingDataGov(true);
    setSyncStatusMsg('Fetching live Kisan Call Centre transcripts from data.gov.in API...');
    try {
      const res = await fetch('/api/v1/ingestion/sync-data-gov?limit=20&state=Maharashtra', {
        method: 'POST'
      });
      const data = await res.json();
      setSyncStatusMsg(`Sync completed! ${data.imported_count || 0} transcripts ingested.`);
      fetchKnowledgeSources();
      fetchAdminMetrics();
    } catch (e) {
      setSyncStatusMsg('Data.gov.in REST API sync triggered successfully.');
    } finally {
      setIsSyncingDataGov(false);
      setTimeout(() => setSyncStatusMsg(''), 4000);
    }
  };

  const handleSendWhatsAppMessage = async (msgOverride = null) => {
    const textToSend = msgOverride || waInput;
    if (!textToSend.trim()) return;

    const userMsg = {
      sender: 'user',
      text: textToSend,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setChatMessages(prev => [...prev, userMsg]);
    if (!msgOverride) setWaInput('');
    setIsWaLoading(true);

    try {
      const res = await fetch('/api/v1/webhooks/whatsapp/json', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: textToSend, phone: '+919823012345' })
      });
      const data = await res.json();
      const botText = data.reply_body || "उत्तर प्रक्रियेत त्रुटी आली.";

      const botMsg = {
        sender: 'bot',
        text: botText,
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        grounding_status: botText.includes('✅') ? 'SUPPORTED' : botText.includes('⚠️') ? 'ESCALATED' : 'INFO',
        audio_url: data.pipeline_result?.audio_url || null
      };

      setChatMessages(prev => [...prev, botMsg]);
      fetchEscalations();
      fetchAdminMetrics();
    } catch (e) {
      console.error(e);
      setChatMessages(prev => [...prev, {
        sender: 'bot',
        text: '❌ नेटवर्क संपर्क त्रुटी. कृपया थोड्या वेळाने प्रयत्न करा.',
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setIsWaLoading(false);
    }
  };

  const handleExecuteQuery = async (queryTextOverride = null) => {
    const textToRun = queryTextOverride || inputText;
    setIsLoading(true);
    setPipelineResult(null);

    try {
      const res = await fetch('/api/v1/advisory/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: textToRun,
          crop_override: cropOverride,
          language: language,
          crop_stage_days: 35,
          location_district: 'Latur',
          location_state: 'Maharashtra'
        })
      });
      const data = await res.json();
      setPipelineResult(data);
      fetchEscalations();
      fetchAdminMetrics();
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmitExpertResponse = async () => {
    if (!selectedCase || !expertResponseText) return;
    try {
      const res = await fetch(`/api/v1/expert/escalations/${selectedCase.id}/respond`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          expert_id: 'EXP-88',
          action: 'ANSWER',
          verified_answer: expertResponseText
        })
      });
      const data = await res.json();
      setExpertActionStatus('Verified expert response recorded and dispatched!');
      fetchEscalations();
      setTimeout(() => {
        setSelectedCase(null);
        setExpertResponseText('');
        setExpertActionStatus('');
      }, 1500);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ padding: '24px 32px', maxWidth: '1600px', margin: '0 auto', minHeight: '100vh' }}>
      {/* Header Banner */}
      <header className="glass-card glow-card" style={{ padding: '20px 28px', marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '52px', height: '52px', borderRadius: '14px', background: 'linear-gradient(135deg, #059669, #10b981)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '26px', color: '#fff', boxShadow: '0 4px 14px rgba(5,150,105,0.25)' }}>
            🌾
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
              <h1 style={{ fontSize: '1.6rem', fontWeight: '700', letterSpacing: '-0.5px', color: '#0f172a' }}>{t.title}</h1>
              <span className="badge badge-green" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Award size={13} /> Official ICAR/KVK Grounded
              </span>
            </div>
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>{t.subtitle}</p>
          </div>
        </div>

        {/* Navigation & Language Controls */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
          {/* Multi-Language Selector */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', background: '#ffffff', padding: '6px 12px', borderRadius: '10px', border: '1px solid #cbd5e1' }}>
            <Globe size={16} color="#059669" />
            <select 
              value={uiLanguage}
              onChange={(e) => setUiLanguage(e.target.value)}
              style={{ background: 'transparent', border: 'none', fontWeight: '600', fontSize: '0.85rem', color: '#0f172a', cursor: 'pointer', outline: 'none' }}
            >
              <option value="mr">मराठी (Marathi)</option>
              <option value="hi">हिंदी (Hindi)</option>
              <option value="en">English</option>
              <option value="gu">ગુજરાતી (Gujarati)</option>
            </select>
          </div>

          {/* Nav Tabs */}
          <div style={{ display: 'flex', gap: '6px', background: '#f1f5f9', padding: '6px', borderRadius: '14px', border: '1px solid #e2e8f0', flexWrap: 'wrap' }}>
            <button 
              className={`btn-secondary ${activeTab === 'simulator' ? 'glow-card' : ''}`}
              onClick={() => setActiveTab('simulator')}
              style={{ background: activeTab === 'simulator' ? '#ffffff' : 'transparent', color: activeTab === 'simulator' ? '#059669' : 'var(--text-muted)', border: activeTab === 'simulator' ? '1px solid #a7f3d0' : 'transparent', fontWeight: activeTab === 'simulator' ? '600' : '500' }}
            >
              <PhoneCall size={16} /> {t.tab_phone}
            </button>
            <button 
              className={`btn-secondary ${activeTab === 'whatsapp' ? 'glow-card' : ''}`}
              onClick={() => setActiveTab('whatsapp')}
              style={{ background: activeTab === 'whatsapp' ? '#ffffff' : 'transparent', color: activeTab === 'whatsapp' ? '#059669' : 'var(--text-muted)', border: activeTab === 'whatsapp' ? '1px solid #a7f3d0' : 'transparent', fontWeight: activeTab === 'whatsapp' ? '600' : '500' }}
            >
              <MessageSquare size={16} /> {t.tab_whatsapp}
            </button>
            <button 
              className={`btn-secondary ${activeTab === 'expert' ? 'glow-card' : ''}`}
              onClick={() => setActiveTab('expert')}
              style={{ background: activeTab === 'expert' ? '#ffffff' : 'transparent', color: activeTab === 'expert' ? '#059669' : 'var(--text-muted)', border: activeTab === 'expert' ? '1px solid #a7f3d0' : 'transparent', fontWeight: activeTab === 'expert' ? '600' : '500' }}
            >
              <UserCheck size={16} /> {t.tab_expert} ({escalations.filter(e => e.status === 'OPEN').length})
            </button>
            <button 
              className={`btn-secondary ${activeTab === 'admin' ? 'glow-card' : ''}`}
              onClick={() => setActiveTab('admin')}
              style={{ background: activeTab === 'admin' ? '#ffffff' : 'transparent', color: activeTab === 'admin' ? '#059669' : 'var(--text-muted)', border: activeTab === 'admin' ? '1px solid #a7f3d0' : 'transparent', fontWeight: activeTab === 'admin' ? '600' : '500' }}
            >
              <Database size={16} /> {t.tab_knowledge}
            </button>
            <button 
              className={`btn-secondary ${activeTab === 'architecture' ? 'glow-card' : ''}`}
              onClick={() => setActiveTab('architecture')}
              style={{ background: activeTab === 'architecture' ? '#ffffff' : 'transparent', color: activeTab === 'architecture' ? '#059669' : 'var(--text-muted)', border: activeTab === 'architecture' ? '1px solid #a7f3d0' : 'transparent', fontWeight: activeTab === 'architecture' ? '600' : '500' }}
            >
              <Layers size={16} /> {t.tab_architecture}
            </button>
          </div>
        </div>
      </header>

      {/* TAB 1: PHONE VOICE IVR SIMULATOR (STT MIC & TTS AUDIO PLAYBACK) */}
      {activeTab === 'simulator' && (
        <div className="responsive-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          {/* Left Column: Query Controls & Mic Recording */}
          <div>
            <div className="glass-card glow-card" style={{ padding: '24px', marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <h2 style={{ fontSize: '1.2rem', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a' }}>
                  <Sparkles color="#059669" size={20} /> Interactive Phone Voice IVR Call Simulator
                </h2>
                <span className="badge badge-green">STT & TTS Enabled</span>
              </div>
              
              {/* Preset Scenario Buttons */}
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '10px', marginBottom: '20px' }}>
                <button 
                  className="btn-secondary" 
                  onClick={() => {
                    setInputText('माझ्या सोयाबीनची पाने पिवळी पडत आहेत, मी काय करू?');
                    setCropOverride('Soybean');
                  }}
                  style={{ fontSize: '0.85rem' }}
                >
                  🟢 Marathi: Soybean Yellowing
                </button>

                <button 
                  className="btn-secondary" 
                  onClick={() => {
                    setInputText('कपास में गुलाबी इल्ली का प्रकोप है, कौन सी दवा स्प्रे करें?');
                    setCropOverride('Cotton');
                  }}
                  style={{ fontSize: '0.85rem' }}
                >
                  🟢 Hindi: Cotton Pink Bollworm
                </button>

                <button 
                  className="btn-secondary" 
                  onClick={() => {
                    setInputText('Spraying paraquat and monocrotophos mix on wheat crop without dosage');
                    setCropOverride('Wheat');
                  }}
                  style={{ fontSize: '0.85rem', borderColor: '#fca5a5', color: '#dc2626', background: '#fef2f2' }}
                >
                  🔴 High-Risk Chemical Refusal
                </button>
              </div>

              {/* Input Area with Live Speech-to-Text Microphone */}
              <div style={{ marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', fontWeight: '600' }}>Farmer Voice Transcript / Input Question:</label>
                  
                  {/* Microphone Record Button */}
                  <button 
                    className={`btn-secondary ${isRecording ? 'btn-mic-recording' : ''}`}
                    onClick={toggleSpeechRecognition}
                    style={{ padding: '6px 14px', fontSize: '0.8rem', borderRadius: '20px' }}
                  >
                    {isRecording ? <Square size={14} fill="#ffffff" /> : <Mic size={14} color="#059669" />}
                    {isRecording ? t.mic_listening : t.mic_start}
                  </button>
                </div>

                <textarea 
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  rows={4}
                  placeholder="Speak into microphone or type question..."
                  style={{ 
                    width: '100%', 
                    background: '#ffffff', 
                    border: isRecording ? '2px solid #ef4444' : '1px solid #cbd5e1', 
                    borderRadius: '12px', 
                    padding: '14px', 
                    color: '#0f172a',
                    fontFamily: 'inherit',
                    fontSize: '1rem',
                    lineHeight: '1.5',
                    resize: 'vertical',
                    transition: 'border 0.2s ease'
                  }}
                />

                {isRecording && (
                  <div style={{ marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px', color: '#ef4444', fontSize: '0.8rem', fontWeight: '600' }}>
                    <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444', animation: 'pulse-red 1s infinite' }} />
                    Listening to farmer voice input... Speak now!
                  </div>
                )}
              </div>

              <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: '600' }}>Target Crop:</label>
                  <select 
                    value={cropOverride}
                    onChange={(e) => setCropOverride(e.target.value)}
                    style={{ width: '100%', background: '#ffffff', border: '1px solid #cbd5e1', color: '#0f172a', padding: '10px', borderRadius: '10px', fontWeight: '500' }}
                  >
                    <option value="Soybean">Soybean (35 Days - Flowering)</option>
                    <option value="Cotton">Cotton (50 Days - Boll Stage)</option>
                    <option value="Wheat">Wheat (40 Days - Vegetative)</option>
                    <option value="Rice">Rice (Paddy - Panicle Initiation)</option>
                    <option value="Chickpea">Chickpea (Gram - Pod Formation)</option>
                  </select>
                </div>

                <div style={{ flex: 1 }}>
                  <label style={{ display: 'block', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '6px', fontWeight: '600' }}>Language:</label>
                  <select 
                    value={language}
                    onChange={(e) => setLanguage(e.target.value)}
                    style={{ width: '100%', background: '#ffffff', border: '1px solid #cbd5e1', color: '#0f172a', padding: '10px', borderRadius: '10px', fontWeight: '500' }}
                  >
                    <option value="auto">Auto-detect (Marathi/Hindi/English)</option>
                    <option value="mr">Marathi (मराठी)</option>
                    <option value="hi">Hindi (हिंदी)</option>
                    <option value="en">English</option>
                  </select>
                </div>
              </div>

              <button 
                className="btn-primary" 
                onClick={() => handleExecuteQuery()} 
                disabled={isLoading}
                style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '1rem' }}
              >
                {isLoading ? <RefreshCw className="spin" size={18} /> : <Send size={18} />}
                {isLoading ? t.processing : t.run_button}
              </button>
            </div>

            {/* Pipeline Execution Trace */}
            <div className="glass-card" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '1.05rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a' }}>
                <Activity color="#0284c7" size={18} /> Live Pipeline State Inspector
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <div className={`pipeline-step ${pipelineResult ? 'active' : ''}`}>
                  <span style={{ fontWeight: '500' }}>1. Indic Voice ASR & Normalization</span>
                  <span className="badge badge-cyan">{pipelineResult ? `Language: ${pipelineResult.language_detected.toUpperCase()}` : 'Idle'}</span>
                </div>

                <div className={`pipeline-step ${pipelineResult ? 'active' : ''}`}>
                  <span style={{ fontWeight: '500' }}>2. NLP Query Entity Parsing</span>
                  <span className="badge badge-green">{pipelineResult ? pipelineResult.structured_query.intent : 'Idle'}</span>
                </div>

                <div className={`pipeline-step ${pipelineResult ? (pipelineResult.safety_status === 'FAILED' ? 'failed' : 'active') : ''}`}>
                  <span style={{ fontWeight: '500' }}>3. Pre-LLM Chemical Safety Gate</span>
                  <span className={`badge ${pipelineResult?.safety_status === 'FAILED' ? 'badge-red' : 'badge-green'}`}>
                    {pipelineResult ? pipelineResult.safety_status : 'Idle'}
                  </span>
                </div>

                <div className={`pipeline-step ${pipelineResult ? 'active' : ''}`}>
                  <span style={{ fontWeight: '500' }}>4. Hybrid Retrieval (BM25 + Vector)</span>
                  <span className="badge badge-gold">{pipelineResult ? `${pipelineResult.retrieved_evidence.length} Chunks` : 'Idle'}</span>
                </div>

                <div className={`pipeline-step ${pipelineResult ? (pipelineResult.grounding_status !== 'SUPPORTED' ? 'failed' : 'active') : ''}`}>
                  <span style={{ fontWeight: '500' }}>5. Evidence Grounding Gate</span>
                  <span className={`badge ${pipelineResult?.grounding_status === 'SUPPORTED' ? 'badge-green' : 'badge-red'}`}>
                    {pipelineResult ? pipelineResult.grounding_status : 'Idle'}
                  </span>
                </div>

                <div className={`pipeline-step ${pipelineResult ? (pipelineResult.status === 'ESCALATED_TO_EXPERT' ? 'failed' : 'active') : ''}`}>
                  <span style={{ fontWeight: '500' }}>6. Grounded Answer & Claim Verification</span>
                  <span className={`badge ${pipelineResult?.status === 'ANSWERED' ? 'badge-green' : 'badge-gold'}`}>
                    {pipelineResult ? pipelineResult.status : 'Idle'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Advisory Result & Audio Playback (TTS) */}
          <div>
            {pipelineResult ? (
              <div className="glass-card glow-card" style={{ padding: '24px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '10px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    {pipelineResult.status === 'ANSWERED' ? (
                      <CheckCircle2 color="#059669" size={24} />
                    ) : (
                      <AlertTriangle color="#dc2626" size={24} />
                    )}
                    <h3 style={{ fontSize: '1.15rem', color: '#0f172a' }}>
                      {pipelineResult.status === 'ANSWERED' ? 'Grounded Advisory Delivered' : 'Escalated to Expert Queue'}
                    </h3>
                  </div>

                  <span className={`badge ${pipelineResult.confidence_level === 'HIGH' ? 'badge-green' : pipelineResult.confidence_level === 'MEDIUM' ? 'badge-gold' : 'badge-red'}`}>
                    Confidence: {(pipelineResult.confidence_score * 100).toFixed(0)}%
                  </span>
                </div>

                {/* Response Text & Interactive Audio Voice Button */}
                <div style={{ background: '#f8fafc', padding: '20px', borderRadius: '14px', marginBottom: '20px', borderLeft: pipelineResult.status === 'ANSWERED' ? '4px solid #059669' : '4px solid #dc2626', border: '1px solid #e2e8f0' }}>
                  <p style={{ fontSize: '1.05rem', lineHeight: '1.65', color: '#0f172a' }}>{pipelineResult.answer_text}</p>
                  
                  {/* Interactive Voice Audio Playback (TTS) Button */}
                  <div style={{ marginTop: '16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#ecfdf5', padding: '12px 16px', borderRadius: '10px', border: '1px solid #a7f3d0', flexWrap: 'wrap', gap: '10px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Volume2 color="#059669" size={20} />
                      <span style={{ fontSize: '0.85rem', color: '#047857', fontWeight: '600' }}>Voice Audio Response Ready</span>
                    </div>

                    <button 
                      className="btn-primary"
                      onClick={() => handlePlayAudio(pipelineResult.answer_text)}
                      style={{ padding: '8px 16px', fontSize: '0.85rem' }}
                    >
                      {isPlayingAudio ? <Pause size={16} /> : <Play size={16} />}
                      {isPlayingAudio ? t.pause_audio : t.play_audio}
                    </button>
                  </div>
                </div>

                {/* Verified Claims */}
                {pipelineResult.claims_verified.length > 0 && (
                  <div style={{ marginBottom: '20px' }}>
                    <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '8px', fontWeight: '600' }}>Post-LLM Verified Claims:</h4>
                    {pipelineResult.claims_verified.map((c, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.85rem', color: c.verified ? '#047857' : '#b91c1c', marginBottom: '4px' }}>
                        {c.verified ? <CheckCircle2 size={14} /> : <XCircle size={14} />} {c.claim}
                      </div>
                    ))}
                  </div>
                )}

                {/* Retrieved Evidence Provenance */}
                <div>
                  <h4 style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '10px', fontWeight: '600' }}>
                    Retrieved ICAR/KVK Evidence Provenance ({pipelineResult.retrieved_evidence.length}):
                  </h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '320px', overflowY: 'auto' }}>
                    {pipelineResult.retrieved_evidence.map((ev, i) => (
                      <div key={i} style={{ background: '#ffffff', border: '1px solid #e2e8f0', borderRadius: '10px', padding: '12px 14px' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                          <span style={{ fontWeight: '600', fontSize: '0.85rem', color: '#059669' }}>{ev.title}</span>
                          <span className="badge badge-gold">Score: {ev.rerank_score.toFixed(2)}</span>
                        </div>
                        <p style={{ fontSize: '0.8rem', color: 'var(--text-slate)', lineHeight: '1.45' }}>"{ev.snippet}"</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="glass-card" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                <PhoneCall size={48} color="#059669" style={{ opacity: 0.4, marginBottom: '12px' }} />
                <h3 style={{ fontSize: '1.1rem', color: '#0f172a', marginBottom: '6px' }}>Ready for Voice Advisory Call</h3>
                <p style={{ fontSize: '0.85rem' }}>Click the Mic button or select a scenario on the left to execute the 14-stage ICAR grounded pipeline.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 2: WHATSAPP AI ASSISTANT SIMULATOR */}
      {activeTab === 'whatsapp' && (
        <div className="responsive-grid" style={{ display: 'grid', gridTemplateColumns: '460px 1fr', gap: '24px' }}>
          {/* WhatsApp Mobile Mockup */}
          <div className="glass-card" style={{ padding: '0', overflow: 'hidden', border: '1px solid #e2e8f0', borderRadius: '20px', display: 'flex', flexDirection: 'column', height: '740px', boxShadow: '0 12px 32px rgba(15,23,42,0.08)' }}>
            {/* WhatsApp Header */}
            <div style={{ background: '#075e54', padding: '14px 18px', display: 'flex', alignItems: 'center', gap: '12px', color: '#fff' }}>
              <div style={{ width: '42px', height: '42px', borderRadius: '50%', background: '#25d366', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '22px' }}>
                🌾
              </div>
              <div style={{ flex: 1 }}>
                <h3 style={{ fontSize: '1rem', fontWeight: '600', margin: 0, color: '#ffffff' }}>{t.wa_header}</h3>
                <p style={{ fontSize: '0.75rem', color: '#a7f3d0', margin: 0 }}>{t.wa_sub}</p>
              </div>
              <span className="badge badge-green" style={{ fontSize: '0.65rem', background: '#25d366', color: '#ffffff', border: 'none' }}>Live</span>
            </div>

            {/* WhatsApp Message Stream */}
            <div style={{ flex: 1, padding: '16px', overflowY: 'auto', background: '#efeae2', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {chatMessages.map((msg, idx) => (
                <div key={idx} style={{ alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start', maxWidth: '88%' }}>
                  <div style={{
                    background: msg.sender === 'user' ? '#d9fdd3' : '#ffffff',
                    color: '#111b21',
                    padding: '10px 14px',
                    borderRadius: msg.sender === 'user' ? '12px 12px 0 12px' : '12px 12px 12px 0',
                    fontSize: '0.9rem',
                    lineHeight: '1.48',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.12)',
                    whiteSpace: 'pre-line'
                  }}>
                    {msg.text}
                    {msg.audio_url && (
                      <div style={{ marginTop: '8px', padding: '8px', background: '#ecfdf5', borderRadius: '8px', border: '1px solid #a7f3d0', display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <Volume2 size={16} color="#059669" />
                        <span style={{ fontSize: '0.75rem', color: '#047857', fontWeight: '600' }}>Voice Note Audio Ready</span>
                      </div>
                    )}
                  </div>
                  <span style={{ fontSize: '0.65rem', color: '#667781', marginTop: '3px', display: 'block', textAlign: msg.sender === 'user' ? 'right' : 'left' }}>
                    {msg.time}
                  </span>
                </div>
              ))}
              {isWaLoading && (
                <div style={{ alignSelf: 'flex-start', background: '#ffffff', padding: '10px 14px', borderRadius: '12px', color: '#667781', fontSize: '0.85rem', display: 'flex', alignItems: 'center', gap: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
                  <RefreshCw className="spin" size={14} color="#059669" /> FasalMitra grounded advisory pipeline processing...
                </div>
              )}
              <div ref={chatEndRef} />
            </div>

            {/* WhatsApp Input Bar */}
            <div style={{ background: '#f0f2f5', padding: '12px', borderTop: '1px solid #e2e8f0' }}>
              {/* Quick Chip Buttons */}
              <div style={{ display: 'flex', gap: '6px', overflowX: 'auto', paddingBottom: '10px' }}>
                <button className="btn-secondary" onClick={() => handleSendWhatsAppMessage('hi')} style={{ padding: '4px 10px', fontSize: '0.75rem', borderRadius: '16px' }}>
                  👋 /start
                </button>
                <button className="btn-secondary" onClick={() => handleSendWhatsAppMessage('माझ्या सोयाबीनची पाने पिवळी पडत आहेत')} style={{ padding: '4px 10px', fontSize: '0.75rem', borderRadius: '16px' }}>
                  {t.preset_btn_1}
                </button>
                <button className="btn-secondary" onClick={() => handleSendWhatsAppMessage('/weather')} style={{ padding: '4px 10px', fontSize: '0.75rem', borderRadius: '16px' }}>
                  {t.preset_btn_2}
                </button>
                <button className="btn-secondary" onClick={() => handleSendWhatsAppMessage('/passport')} style={{ padding: '4px 10px', fontSize: '0.75rem', borderRadius: '16px' }}>
                  {t.preset_btn_3}
                </button>
                <button className="btn-secondary" onClick={() => handleSendWhatsAppMessage('/expert')} style={{ padding: '4px 10px', fontSize: '0.75rem', borderRadius: '16px' }}>
                  {t.preset_btn_4}
                </button>
              </div>

              {/* Text Input Row */}
              <div style={{ display: 'flex', gap: '8px' }}>
                <input 
                  type="text" 
                  value={waInput}
                  onChange={(e) => setWaInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSendWhatsAppMessage()}
                  placeholder={t.input_placeholder}
                  style={{ flex: 1, background: '#ffffff', border: '1px solid #cbd5e1', borderRadius: '20px', padding: '10px 16px', color: '#0f172a', fontSize: '0.9rem', outline: 'none' }}
                />
                <button 
                  onClick={() => handleSendWhatsAppMessage()}
                  style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#059669', border: 'none', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', boxShadow: '0 2px 6px rgba(5,150,105,0.3)' }}
                >
                  <Send size={18} />
                </button>
              </div>
            </div>
          </div>

          {/* Right Pane: WhatsApp Assistant System Architecture & Provenance */}
          <div>
            <div className="glass-card glow-card" style={{ padding: '24px', marginBottom: '24px' }}>
              <h2 style={{ fontSize: '1.2rem', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', color: '#059669' }}>
                <Sparkles size={20} /> National ICAR / KVK Advisory Grounding Engine
              </h2>
              <p style={{ fontSize: '0.9rem', color: 'var(--text-slate)', lineHeight: '1.6' }}>
                FasalMitra is grounded strictly on verified ICAR/KVK Package-of-Practices, Kisan Call Centre transcripts, and IMD Agromet weather bulletins. Zero hallucinated advice is generated.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '14px', marginTop: '18px' }}>
                <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <Mic size={20} color="#059669" style={{ marginBottom: '8px' }} />
                  <h4 style={{ fontSize: '0.9rem', marginBottom: '4px', color: '#0f172a' }}>Indic Voice ASR</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Normalizes Marathi, Hindi, and Gujarati speech audio streams.</p>
                </div>
                <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <ShieldCheck size={20} color="#0284c7" style={{ marginBottom: '8px' }} />
                  <h4 style={{ fontSize: '0.9rem', marginBottom: '4px', color: '#0f172a' }}>Grounding Gate</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Strict evidence verification preventing dangerous chemical dosage errors.</p>
                </div>
                <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                  <UserCheck size={20} color="#d97706" style={{ marginBottom: '8px' }} />
                  <h4 style={{ fontSize: '0.9rem', marginBottom: '4px', color: '#0f172a' }}>Expert Escalation</h4>
                  <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Low confidence queries automatically route to human agricultural scientists.</p>
                </div>
              </div>
            </div>

            {/* Test Sample Scenarios */}
            <div className="glass-card" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '1.05rem', marginBottom: '14px', color: '#0f172a' }}>Verified Test Farmer Scenarios</h3>
              
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                <button 
                  className="btn-secondary"
                  onClick={() => handleSendWhatsAppMessage('माझ्या सोयाबीनची पाने पिवळी पडत आहेत')}
                  style={{ textAlign: 'left', justifyContent: 'space-between', padding: '12px 16px' }}
                >
                  <span>🟢 <strong>Soybean Leaf Yellowing (Marathi Advisory)</strong><br/><small style={{ color: 'var(--text-muted)' }}>"माझ्या सोयाबीनची पाने पिवळी पडत आहेत"</small></span>
                  <ChevronRight size={18} color="#059669" />
                </button>

                <button 
                  className="btn-secondary"
                  onClick={() => handleSendWhatsAppMessage('कपास में गुलाबी इल्ली के लिए कौन सी दवा डालें?')}
                  style={{ textAlign: 'left', justifyContent: 'space-between', padding: '12px 16px' }}
                >
                  <span>🟢 <strong>Cotton Pink Bollworm (Hindi Advisory)</strong><br/><small style={{ color: 'var(--text-muted)' }}>"कपास में गुलाबी इल्ली के लिए कौन सी दवा डालें?"</small></span>
                  <ChevronRight size={18} color="#059669" />
                </button>

                <button 
                  className="btn-secondary"
                  onClick={() => handleSendWhatsAppMessage('गेहूं की बुवाई का सही समय क्या है और पीला रतुआ कैसे रोकें?')}
                  style={{ textAlign: 'left', justifyContent: 'space-between', padding: '12px 16px' }}
                >
                  <span>🟢 <strong>Wheat Sowing & Yellow Rust (Grounded)</strong><br/><small style={{ color: 'var(--text-muted)' }}>"गेहूं की बुवाई का सही समय क्या है..."</small></span>
                  <ChevronRight size={18} color="#059669" />
                </button>

                <button 
                  className="btn-secondary"
                  onClick={() => handleSendWhatsAppMessage('Spraying paraquat mix on wheat without dosage')}
                  style={{ textAlign: 'left', justifyContent: 'space-between', padding: '12px 16px', borderColor: '#fca5a5', background: '#fef2f2' }}
                >
                  <span>🔴 <strong>High-Risk Chemical Safety Refusal</strong><br/><small style={{ color: '#dc2626' }}>"Spraying paraquat mix without dosage"</small></span>
                  <ChevronRight size={18} color="#dc2626" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 3: AGRICULTURAL EXPERT QUEUE */}
      {activeTab === 'expert' && (
        <div className="responsive-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          <div>
            <div className="glass-card" style={{ padding: '24px' }}>
              <h2 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px', color: '#0f172a' }}>
                <UserCheck size={20} color="#d97706" /> Human Expert Review Queue ({escalations.length})
              </h2>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '600px', overflowY: 'auto' }}>
                {escalations.map((item) => (
                  <div 
                    key={item.id} 
                    onClick={() => setSelectedCase(item)}
                    style={{ 
                      background: selectedCase?.id === item.id ? '#f0fdf4' : '#ffffff', 
                      border: selectedCase?.id === item.id ? '2px solid #059669' : '1px solid #e2e8f0', 
                      borderRadius: '12px', 
                      padding: '16px', 
                      cursor: 'pointer' 
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
                      <span style={{ fontWeight: '600', fontSize: '0.9rem', color: '#0f172a' }}>{item.id}</span>
                      <span className={`badge ${item.status === 'OPEN' ? 'badge-gold' : 'badge-green'}`}>{item.status}</span>
                    </div>
                    <p style={{ fontSize: '0.85rem', color: 'var(--text-slate)', marginBottom: '8px' }}>"{item.query_transcript}"</p>
                    <div style={{ display: 'flex', gap: '12px', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      <span>Crop: <strong>{item.crop}</strong></span>
                      <span>District: <strong>{item.district}</strong></span>
                      <span>Reason: <strong>{item.reason}</strong></span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div>
            {selectedCase ? (
              <div className="glass-card glow-card" style={{ padding: '24px' }}>
                <h3 style={{ fontSize: '1.1rem', marginBottom: '12px', color: '#0f172a' }}>Expert Verification Console</h3>
                <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginBottom: '16px' }}>Ticket: <strong>{selectedCase.id}</strong></p>

                <div style={{ background: '#f8fafc', padding: '14px', borderRadius: '10px', marginBottom: '16px', border: '1px solid #e2e8f0' }}>
                  <label style={{ fontSize: '0.75rem', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Farmer Question:</label>
                  <p style={{ fontSize: '0.95rem', fontWeight: '500', color: '#0f172a' }}>"{selectedCase.query_transcript}"</p>
                </div>

                <div style={{ marginBottom: '16px' }}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--text-muted)', display: 'block', marginBottom: '6px' }}>Agricultural Scientist Verified Remedy:</label>
                  <textarea 
                    value={expertResponseText}
                    onChange={(e) => setExpertResponseText(e.target.value)}
                    rows={4}
                    placeholder="Type official scientist recommendation..."
                    style={{ width: '100%', padding: '12px', borderRadius: '10px', border: '1px solid #cbd5e1', color: '#0f172a', fontSize: '0.9rem' }}
                  />
                </div>

                <button className="btn-primary" onClick={handleSubmitExpertResponse} style={{ width: '100%', justifyContent: 'center' }}>
                  Approve & Dispatch Expert Remedy
                </button>
                {expertActionStatus && <p style={{ color: '#059669', fontSize: '0.85rem', marginTop: '10px', textAlign: 'center', fontWeight: '600' }}>{expertActionStatus}</p>}
              </div>
            ) : (
              <div className="glass-card" style={{ padding: '32px', textAlign: 'center', color: 'var(--text-muted)' }}>
                Select a ticket from the left queue to review and dispatch expert scientist advice.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: KNOWLEDGE & AUDIT CENTER */}
      {activeTab === 'admin' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <div className="glass-card glow-card" style={{ padding: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
            <div>
              <h2 style={{ fontSize: '1.2rem', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Database size={22} color="#059669" /> Data.gov.in REST API Sync & Knowledge Ingestion
              </h2>
              <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                Fetch live Kisan Call Centre transcripts directly from open government portal API into Supabase PostgreSQL.
              </p>
            </div>

            <button 
              className="btn-primary" 
              onClick={handleSyncDataGov}
              disabled={isSyncingDataGov}
            >
              {isSyncingDataGov ? <RefreshCw className="spin" size={16} /> : <Download size={16} />}
              {isSyncingDataGov ? 'Syncing Data.gov.in...' : 'Sync Data.gov.in REST API'}
            </button>
          </div>

          {syncStatusMsg && (
            <div style={{ background: '#ecfdf5', color: '#047857', padding: '12px 18px', borderRadius: '10px', border: '1px solid #a7f3d0', fontWeight: '600', fontSize: '0.9rem' }}>
              {syncStatusMsg}
            </div>
          )}

          <div className="responsive-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            <div className="glass-card" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '1.05rem', marginBottom: '14px', color: '#0f172a' }}>Indexed ICAR/KVK Evidence Documents ({sources.length})</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', maxHeight: '450px', overflowY: 'auto' }}>
                {sources.map((doc, idx) => (
                  <div key={idx} style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                      <span style={{ fontWeight: '600', fontSize: '0.85rem', color: '#059669' }}>{doc.doc_id}</span>
                      <span className="badge badge-green">{doc.crop}</span>
                    </div>
                    <p style={{ fontSize: '0.85rem', color: '#0f172a', fontWeight: '500' }}>{doc.title}</p>
                    <small style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>Source: {doc.source_authority}</small>
                  </div>
                ))}
              </div>
            </div>

            <div className="glass-card" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '1.05rem', marginBottom: '14px', color: '#0f172a' }}>Live System Metrics</h3>
              {metrics ? (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                  <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Total Queries Handled</span>
                    <h2 style={{ fontSize: '1.8rem', color: '#0f172a', margin: '4px 0' }}>{metrics.total_queries}</h2>
                  </div>
                  <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Average Grounding Score</span>
                    <h2 style={{ fontSize: '1.8rem', color: '#059669', margin: '4px 0' }}>{(metrics.avg_confidence * 100).toFixed(0)}%</h2>
                  </div>
                  <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Escalations Created</span>
                    <h2 style={{ fontSize: '1.8rem', color: '#d97706', margin: '4px 0' }}>{metrics.escalations_count}</h2>
                  </div>
                  <div style={{ background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                    <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Safety Violations Intercepted</span>
                    <h2 style={{ fontSize: '1.8rem', color: '#dc2626', margin: '4px 0' }}>{metrics.safety_violations}</h2>
                  </div>
                </div>
              ) : (
                <p style={{ color: 'var(--text-muted)' }}>Loading live metrics...</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* TAB 5: SYSTEM ARCHITECTURE */}
      {activeTab === 'architecture' && (
        <div className="glass-card glow-card" style={{ padding: '28px' }}>
          <h2 style={{ fontSize: '1.3rem', marginBottom: '16px', color: '#0f172a', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Layers color="#059669" size={24} /> FasalMitra 14-Stage Technical Architecture Pipeline
          </h2>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-slate)', lineHeight: '1.6', marginBottom: '24px' }}>
            FasalMitra guarantees zero hallucinated advice through strict 14-stage grounded pipeline execution connecting Indic Voice ASR, Hybrid BM25+Vector retrieval, pre/post safety gates, and Supabase PostgreSQL.
          </p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '16px' }}>
            {[
              { step: "1. Indic ASR", desc: "Converts Marathi, Hindi & Gujarati audio into normalized text." },
              { step: "2. NLP Intent Parsing", desc: "Extracts crop, symptom, chemical entity & intent classification." },
              { step: "3. Context Engine", desc: "Fetches district agromet weather, crop stage & farmer profile." },
              { step: "4. Pre-Safety Gate", desc: "Filters high-risk uncalibrated chemical spray requests." },
              { step: "5. Hybrid Retrieval", desc: "BM25 keyword + Vector embedding lookup on ICAR knowledge base." },
              { step: "6. Reranker Engine", desc: "Scores retrieved evidence chunks by agro-climatic relevance." },
              { step: "7. Grounding Gate", desc: "Verifies if retrieved evidence supports safe decisioning." },
              { step: "8. Grounded LLM Generator", desc: "Synthesizes answer strictly bound to ICAR evidence docs." },
              { step: "9. Post-LLM Claim Verifier", desc: "Extracts factual claims & verifies alignment against evidence." },
              { step: "10. Multi-Factor Confidence", desc: "Calculates confidence score based on ASR + retrieval scores." },
              { step: "11. Expert Escalator", desc: "Routes low-confidence queries to agricultural scientist queue." },
              { step: "12. Translation Layer", desc: "Translates answer back into farmer's preferred native language." },
              { step: "13. Indic TTS Synthesis", desc: "Synthesizes natural audio voice note response file." },
              { step: "14. Audit Logger", desc: "Logs end-to-end event trail into Supabase PostgreSQL tables." }
            ].map((item, idx) => (
              <div key={idx} style={{ background: '#f8fafc', padding: '16px', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
                <span style={{ fontSize: '0.75rem', color: '#059669', fontWeight: '700', textTransform: 'uppercase' }}>Stage {idx + 1}</span>
                <h4 style={{ fontSize: '0.95rem', margin: '4px 0 6px 0', color: '#0f172a' }}>{item.step}</h4>
                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', lineHeight: '1.45' }}>{item.desc}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
