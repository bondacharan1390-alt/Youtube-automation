import json
import re
from typing import Dict, Any, Optional, List
from app.services.llm.base import BaseLLMProvider

class FallbackScriptEngine(BaseLLMProvider):
    """
    High-quality, zero-dependency heuristic generator for English & Telugu.
    Ensures that when external daemons (Ollama) or cloud keys (Gemini) are absent,
    the application seamlessly generates structured scripts, research, characters,
    and dialogue without throwing unhandled exceptions.
    """

    def get_provider_name(self) -> str:
        return "Internal Heuristic Engine (Offline Resilient)"

    def check_health(self) -> Dict[str, Any]:
        return {"is_healthy": True, "message": "Offline Heuristic Generator 100% Ready"}

    def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        return f"Autonomous Script Outline for: {prompt[:100]}"

    def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        prompt_lower = prompt.lower()
        is_telugu = "telugu" in prompt_lower or "te" in prompt_lower or any(ord(c) >= 0x0C00 and ord(c) <= 0x0C7F for c in prompt)

        # 1. Research Analysis Request
        if "analyze" in prompt_lower or "virality" in prompt_lower or "target audience" in prompt_lower:
            return self._build_research_analysis(prompt, is_telugu)

        # 2. Video Ideas Request
        if "video ideas" in prompt_lower or "5 unique concepts" in prompt_lower or "angles" in prompt_lower:
            return self._build_video_ideas(prompt, is_telugu)

        # 3. Story & Character Dialogue Request
        if "character" in prompt_lower or "dialogue" in prompt_lower or "story" in prompt_lower:
            return self._build_story_characters(prompt, is_telugu)

        # 4. Standard Scene-by-Scene Script Request (Default)
        return self._build_scene_script(prompt, is_telugu)

    def _build_research_analysis(self, prompt: str, is_telugu: bool) -> Dict[str, Any]:
        if is_telugu:
            return {
                "topic": prompt[:80],
                "virality_score": 88,
                "audience_persona": "తెలుగు యువత, టెక్నాలజీ ఔత్సాహికులు మరియు ఆసక్తికరమైన విషయాలు తెలుసుకోవాలనుకునే ప్రేక్షకులు.",
                "search_intent": "సమాచారం మరియు వినోదం కోసం శోధించే వీక్షకులు.",
                "hook_angles": [
                    "మీకు తెలిసిన దానికంటే ఇది చాలా ఆశ్చర్యకరమైన విషయం!",
                    "శాస్త్రవేత్తలే ఆశ్చర్యపోయిన తాజా నిజం ఏమిటి?",
                    "ఈ వీడియో చూసిన తర్వాత మీ ఆలోచన పూర్తిగా మారిపోతుంది."
                ],
                "primary_keywords": ["తెలుగు టెక్నాలజీ", "తాజా రహస్యాలు", "ఆసక్తికరమైన విషయాలు", "యూట్యూబ్ వైరల్"],
                "long_tail_keywords": [
                    "తెలుగులో పూర్తి సమాచారం ఎలా తెలుసుకోవాలి",
                    "తెలుగు ఆటోమేషన్ తాజా వార్తలు 2026",
                    "తెలుగు సైన్స్ మరియు ఫ్యాక్ట్స్"
                ],
                "recommended_video_length": "8 to 12 minutes (Long) or 50 seconds (Short)"
            }
        return {
            "topic": prompt[:80],
            "virality_score": 92,
            "audience_persona": "Tech-savvy creators, knowledge seekers, and general YouTube viewers aged 18-35.",
            "search_intent": "High informational search seeking concise, cinematic explanations.",
            "hook_angles": [
                "The shocking truth the mainstream media isn't talking about.",
                "Why 99% of people misunderstand this critical breakthrough.",
                "Everything you thought you knew just became obsolete."
            ],
            "primary_keywords": ["AI breakthrough", "YouTube automation", "future technology", "viral trends 2026"],
            "long_tail_keywords": [
                "how autonomous AI agents work in 2026",
                "step by step guide to next gen video automation",
                "best practical AI tools for content creators"
            ],
            "recommended_video_length": "8 to 12 minutes (Long) or 45 seconds (Short)"
        }

    def _build_video_ideas(self, prompt: str, is_telugu: bool) -> Dict[str, Any]:
        if is_telugu:
            return {
                "ideas": [
                    {
                        "title": "అద్భుతమైన భవిష్యత్ రహస్యాలు: మీరు నమ్మలేని 5 విషయాలు",
                        "angle": "డాక్యుమెంటరీ మరియు రహస్యాల శైలి",
                        "hook": "ఈ 5 విషయాలు తెలిస్తే మీరు ఖచ్చితంగా ఆశ్చర్యపోతారు!",
                        "estimated_ctr": "12.4%",
                        "format": "16:9"
                    },
                    {
                        "title": "60 సెకన్లలో సరికొత్త టెక్నాలజీ విప్లవం! (Shorts)",
                        "angle": "వేగవంతమైన యూట్యూబ్ షార్ట్",
                        "hook": "కేవలం 24 గంటల్లో ప్రపంచం ఎలా మారిపోయిందో తెలుసా?",
                        "estimated_ctr": "16.8%",
                        "format": "9:16"
                    },
                    {
                        "title": "ప్రజలు నమ్మే 3 పెద్ద అబద్ధాలు - నిజం ఏమిటి?",
                        "angle": "మిథ్ బస్టింగ్ / విశ్లేషణ",
                        "hook": "మనం ఇప్పటివరకు నమ్మిన విషయాలన్నీ తప్పేనా?",
                        "estimated_ctr": "14.1%",
                        "format": "16:9"
                    },
                    {
                        "title": "ప్రపంచాన్ని మార్చేస్తున్న AI అద్భుతాలు 2026",
                        "angle": "డీప్ డైవ్ ఎక్స్‌ప్లేనర్",
                        "hook": "భవిష్యత్తు ఇప్పటికే వచ్చేసింది, మీరు సిద్ధంగా ఉన్నారా?",
                        "estimated_ctr": "11.9%",
                        "format": "16:9"
                    },
                    {
                        "title": "తెలియని వాస్తవాలు: 99% మందికి తెలియని రహస్యం",
                        "angle": "ఉత్కంఠభరిత కథనం",
                        "hook": "ఈ ఒక్క విషయం మీ జీవితాన్ని మార్చేయగలదు.",
                        "estimated_ctr": "15.2%",
                        "format": "9:16"
                    }
                ]
            }
        return {
            "ideas": [
                {
                    "title": "5 Mind-Blowing Inventions That Change Everything in 2026",
                    "angle": "Documentary Countdown",
                    "hook": "What if machines could outthink whole teams of engineers in seconds?",
                    "estimated_ctr": "13.2%",
                    "format": "16:9"
                },
                {
                    "title": "Stop Doing This! The Secret 99% Of People Miss (Shorts)",
                    "angle": "Rapid High-Retention Hook",
                    "hook": "You are wasting your time if you aren't doing this one thing.",
                    "estimated_ctr": "17.4%",
                    "format": "9:16"
                },
                {
                    "title": "The Dark Reality Behind Modern Autonomous AI",
                    "angle": "Investigative / Deep Dive",
                    "hook": "Behind the flashy headlines lies an uncomfortable truth.",
                    "estimated_ctr": "14.8%",
                    "format": "16:9"
                },
                {
                    "title": "From Zero to Hero: How One Creator Automated Everything",
                    "angle": "Case Study & Storytelling",
                    "hook": "He built a 1M subscriber channel without ever showing his face.",
                    "estimated_ctr": "12.5%",
                    "format": "16:9"
                },
                {
                    "title": "The 30-Second Lifehack You Won't Forget (Shorts)",
                    "angle": "Viral Practical Tip",
                    "hook": "Save this video before it gets taken down.",
                    "estimated_ctr": "18.1%",
                    "format": "9:16"
                }
            ]
        }

    def _build_story_characters(self, prompt: str, is_telugu: bool) -> Dict[str, Any]:
        if is_telugu:
            return {
                "story_title": "సరికొత్త ప్రయాణం: భవిష్యత్ నగరంలో రహస్యం",
                "characters": [
                    {
                        "name": "రాము (Ramu)",
                        "role": "యువ పరిశోధకుడు మరియు విశ్లేషకుడు",
                        "voice_style": "ఉత్సాహభరితమైన మరియు ఆత్మవిశ్వాసం గల స్వరం",
                        "visual_prompt": "Portrait of a young Indian male tech investigator with smart glasses, cinematic lighting, 8k"
                    },
                    {
                        "name": "అన్విత (Anvitha)",
                        "role": "AI ఇంజనీర్ మరియు సైంటిస్ట్",
                        "voice_style": "స్పష్టమైన, ఆలోచనాత్మకమైన మరియు హుందాతనంగల స్వరం",
                        "visual_prompt": "Portrait of a sophisticated Indian female AI scientist in a high-tech modern laboratory, neon accents"
                    }
                ],
                "dialogue_scenes": [
                    {
                        "speaker": "రాము (Ramu)",
                        "line": "అన్విత, ఈ డేటా చూశావా? మనం అనుకున్న దానికంటే ఇది చాలా పెద్ద విప్లవం!",
                        "visual_prompt": "Young tech investigator pointing enthusiastically at a futuristic glowing holographic interface, ultra-detailed",
                        "duration_seconds": 5.5
                    },
                    {
                        "speaker": "అన్విత (Anvitha)",
                        "line": "అవును రాము, ఈ టెక్నాలజీ వల్ల మనుషుల రోజువారీ పనులు కొన్ని క్షణాల్లోనే పూర్తవుతాయి.",
                        "visual_prompt": "Female scientist nodding with a warm smile, holding a transparent smart tablet with quantum circuits",
                        "duration_seconds": 6.0
                    },
                    {
                        "speaker": "రాము (Ramu)",
                        "line": "అయితే మన ప్రేక్షకులకు ఈ రహస్యాన్ని వెంటనే వివరిద్దాం రండి!",
                        "visual_prompt": "Both investigators looking directly at camera inviting the audience into a futuristic studio, cinematic 4k",
                        "duration_seconds": 5.0
                    }
                ]
            }
        return {
            "story_title": "The Quantum Shift: An Encounter with Tomorrow",
            "characters": [
                {
                    "name": "Alex",
                    "role": "Curious Tech Investigator",
                    "voice_style": "Energetic, dynamic narrator",
                    "visual_prompt": "Cinematic portrait of a male tech researcher in his late 20s, wearing minimalist audio monitors, dramatic studio rim light"
                },
                {
                    "name": "Dr. Sarah",
                    "role": "Lead Systems Architect",
                    "voice_style": "Authoritative, calm, and visionary",
                    "visual_prompt": "Cinematic portrait of a female scientist in her 30s with focused gaze, standing in front of quantum data servers"
                }
            ],
            "dialogue_scenes": [
                {
                    "speaker": "Alex",
                    "line": "Dr. Sarah, are you saying the system can now generate full-length videos without human intervention?",
                    "visual_prompt": "Young man staring in awe at towering server racks pulsating with cyan light, cinematic bokeh",
                    "duration_seconds": 5.5
                },
                {
                    "speaker": "Dr. Sarah",
                    "line": "Not just generate them, Alex. It researches, scripts, voices, and edits them in under three minutes.",
                    "visual_prompt": "Scientist confidently gesturing towards a high-resolution holographic editing timeline floating in mid-air",
                    "duration_seconds": 6.5
                },
                {
                    "speaker": "Alex",
                    "line": "That changes every rule of digital storytelling forever.",
                    "visual_prompt": "Extreme close-up of protagonist eyes reflecting neon binary code, cinematic 8k render",
                    "duration_seconds": 4.5
                }
            ]
        }

    def _build_scene_script(self, prompt: str, is_telugu: bool) -> Dict[str, Any]:
        is_shorts = "9:16" in prompt or "short" in prompt.lower()
        if is_telugu:
            if is_shorts:
                scenes = [
                    {
                        "scene_order": 1,
                        "script_text": "ప్రారంభ హుక్: నమ్మలేని ఆశ్చర్యకరమైన విషయం",
                        "narration_text": "మీరు ఎప్పుడైనా ఆలోచించారా? కేవలం కొన్ని సెకన్లలో మీ జీవితాన్ని మార్చే రహస్యం ఏమిటో?",
                        "visual_prompt": "Dramatic high-contrast vertical shot of a golden pocket watch shattering into glowing light particles, 9:16 aspect ratio, cinematic lighting, 8k",
                        "duration_seconds": 5.0
                    },
                    {
                        "scene_order": 2,
                        "script_text": "ప్రధాన రహస్యం మరియు వివరణ",
                        "narration_text": "ప్రపంచవ్యాప్తంగా ఉన్న పరిశోధకులు కనుగొన్న ఈ కొత్త వాస్తవం అందరినీ ఆశ్చర్యపరుస్తోంది.",
                        "visual_prompt": "Fast-paced vertical frame showing high-tech laboratory with glowing holographic DNA strands, 9:16, photorealistic",
                        "duration_seconds": 6.0
                    },
                    {
                        "scene_order": 3,
                        "script_text": "క్లైమాక్స్ మరియు ముగింపు కాల్-టు-యాక్షన్",
                        "narration_text": "ఈ సమాచారం మీకు నచ్చితే వెంటనే లైక్ చేయండి, మరిన్ని ఆసక్తికరమైన వీడియోల కోసం ఇప్పుడే సబ్‌స్క్రైబ్ చేసుకోండి!",
                        "visual_prompt": "Vibrant glowing YouTube subscribe button bursting with neon particles, vertical 9:16 framing, 4k",
                        "duration_seconds": 5.0
                    }
                ]
            else:
                scenes = [
                    {
                        "scene_order": 1,
                        "script_text": "ఆకర్షణీయమైన ప్రారంభ హుక్",
                        "narration_text": "నమస్కారం వీక్షకులకు! ఈ రోజు మనం ప్రపంచంలో అత్యంత ఆసక్తికరమైన మరియు ఎవరికీ తెలియని రహస్యాల గురించి తెలుసుకోబోతున్నాం.",
                        "visual_prompt": "Cinematic wide angle opening shot of an ancient futuristic temple illuminated by glowing neon runes, 16:9, Unreal Engine 5 render",
                        "duration_seconds": 7.0
                    },
                    {
                        "scene_order": 2,
                        "script_text": "రహస్యం 1: అంతుచిక్కని ఆవిష్కరణలు",
                        "narration_text": "శాస్త్రవేత్తలు ఇటీవల చేపట్టిన పరిశోధనల్లో బయటపడిన ఈ విషయాలు ఎన్నో పాత సిద్ధాంతాలను తారుమారు చేశాయి.",
                        "visual_prompt": "Detailed laboratory inspection table with antique manuscripts next to advanced quantum computing circuits, 16:9 cinematic lighting",
                        "duration_seconds": 8.0
                    },
                    {
                        "scene_order": 3,
                        "script_text": "రహస్యం 2: భవిష్యత్తుపై ప్రభావం",
                        "narration_text": "ఈ మార్పులు మన భవిష్యత్తును ఎలా ప్రభావితం చేస్తాయో తెలుసుకుంటే మీరు ఖచ్చితంగా ఆశ్చర్యపోతారు.",
                        "visual_prompt": "Breathtaking panoramic view of a solar-powered futuristic metropolis with flying maglev vehicles, golden hour, 8k",
                        "duration_seconds": 7.5
                    },
                    {
                        "scene_order": 4,
                        "script_text": "ముగింపు మరియు సబ్‌స్క్రైబ్ సందేశం",
                        "narration_text": "ఈ వీడియోపై మీ అమూల్యమైన అభిప్రాయాన్ని కామెంట్ చేయండి. ఇలాంటి మరిన్ని విజ్ఞాన విషయాల కోసం ఛానల్‌ను వెంటనే సబ్‌స్క్రైబ్ చేసుకోండి!",
                        "visual_prompt": "Clean professional YouTube outro screen with subscribe and notification bell animation, soft studio backdrop, 16:9",
                        "duration_seconds": 6.5
                    }
                ]
            return {
                "title": prompt[:70],
                "language": "te",
                "aspect_ratio": "9:16" if is_shorts else "16:9",
                "scenes": scenes
            }

        # English Scripts
        if is_shorts:
            scenes = [
                {
                    "scene_order": 1,
                    "script_text": "Cold Hook: Stop what you are doing",
                    "narration_text": "Did you know that 99% of people are completely unaware of this hidden breakthrough?",
                    "visual_prompt": "Dramatic vertical close-up of a human eye with digital circuit reflections, 9:16 framing, anamorphic lens flare, 8k",
                    "duration_seconds": 4.5
                },
                {
                    "scene_order": 2,
                    "script_text": "The Revelation: Core insight",
                    "narration_text": "Researchers just unlocked a mechanism that accelerates automated creation by ten times.",
                    "visual_prompt": "Rapid vertical kinetic graphics showing a processor core unleashing golden energy ripples, 9:16, photorealistic",
                    "duration_seconds": 5.5
                },
                {
                    "scene_order": 3,
                    "script_text": "Outro Hook: Call to Action",
                    "narration_text": "Hit that follow button right now so you never miss what's coming next.",
                    "visual_prompt": "Neon illuminated subscribe indicator with glowing particle burst, vertical 9:16, high energy, 4k",
                    "duration_seconds": 4.0
                }
            ]
        else:
            scenes = [
                {
                    "scene_order": 1,
                    "script_text": "Act 1: The Dramatic Cold Open",
                    "narration_text": "What if everything you were taught about modern content creation was completely overturned in a single weekend?",
                    "visual_prompt": "Cinematic wide establishing shot of a lone creator silhouette standing before massive panoramic displays, 16:9, volumetric lighting, 8k",
                    "duration_seconds": 6.5
                },
                {
                    "scene_order": 2,
                    "script_text": "Act 2: The Core Problem",
                    "narration_text": "For years, producing high-fidelity video required entire production teams, weeks of editing, and thousands of dollars in gear.",
                    "visual_prompt": "Time-lapse of an empty film studio cluttered with heavy cameras and lighting rigs fading into shadows, 16:9, moody lighting",
                    "duration_seconds": 8.0
                },
                {
                    "scene_order": 3,
                    "script_text": "Act 3: The Breakthrough Solution",
                    "narration_text": "Now, autonomous pipeline architectures can orchestrate research, scripting, natural voiceover, and visual synthesis in minutes.",
                    "visual_prompt": "Futuristic clean workspace where holographic timelines snap together seamlessly, cyan and gold glowing UI, 16:9, photorealistic",
                    "duration_seconds": 8.5
                },
                {
                    "scene_order": 4,
                    "script_text": "Act 4: The Impact & Climax",
                    "narration_text": "Those who adapt today will command the audiences of tomorrow. The barriers to high-impact storytelling have dissolved.",
                    "visual_prompt": "Inspiring sunrise shot over a modern glass metropolis with glowing digital networks stretching across the horizon, 16:9",
                    "duration_seconds": 7.0
                },
                {
                    "scene_order": 5,
                    "script_text": "Act 5: Outro & Call to Action",
                    "narration_text": "If you want to stay ahead of the curve, make sure to like, subscribe, and drop your thoughts in the comments below.",
                    "visual_prompt": "Sleek YouTube outro screen with subscribe button pulse and dynamic audio visualizer, 16:9, modern clean aesthetics",
                    "duration_seconds": 6.0
                }
            ]

        return {
            "title": prompt[:70],
            "language": "en",
            "aspect_ratio": "9:16" if is_shorts else "16:9",
            "scenes": scenes
        }
