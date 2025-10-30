import json
from datetime import datetime
import os
import google.generativeai as genai
from dotenv import load_dotenv
import re

class StressEstimator:
    def __init__(self, use_database=True, use_llm=True):
        self.use_llm = use_llm
        self.llm_client = None
        
        print(f"🔧 Initializing StressEstimator - use_llm: {use_llm}")
        
        # Gemini configuration
        if use_llm:
            self.llm_client = self._setup_gemini()
            if self.llm_client:
                print("✅ Gemini client initialized successfully")
                self.use_llm = True
            else:
                print("❌ Gemini setup failed, using rule-based analysis")
                self.use_llm = False
        
        # Database integration
        self.use_database = use_database
        if use_database:
            try:
                from database.sqlite_manager import DatabaseManager
                self.db_manager = DatabaseManager()
                print("✅ Database initialized")
            except Exception as e:
                print(f"❌ Database initialization failed: {e}")
                self.use_database = False
    
    def _setup_gemini(self):
        """Setup Gemini client with automatic model detection"""
        try:
            load_dotenv()
            api_key = os.getenv('GOOGLE_API_KEY')
            
            if not api_key:
                print("❌ GOOGLE_API_KEY not found in environment variables")
                return None
            
            print(f"🔑 API Key found: {api_key[:12]}...")
            
            # Configure Gemini
            genai.configure(api_key=api_key)
            
            # Get available models
            print("🤖 Discovering available models...")
            available_models = genai.list_models()
            
            # Filter for Gemini text models
            gemini_models = []
            for model in available_models:
                if 'gemini' in model.name.lower() and 'generateContent' in model.supported_generation_methods:
                    gemini_models.append(model.name)
                    print(f"   ✅ {model.name}")
            
            if not gemini_models:
                print("❌ No compatible Gemini models found")
                return None
            
            # Try models in order of preference
            preferred_models = [
                'models/gemini-2.0-flash-001',  # Fast and capable
                'models/gemini-2.0-flash',      # Alternative flash
                'models/gemini-2.5-flash',      # Latest flash
                'models/gemini-2.5-pro',        # Pro version
                'models/gemini-2.0-flash-lite-001',  # Lite version
            ]
            
            # Filter to only available models
            available_preferred = [model for model in preferred_models if model in gemini_models]
            
            if not available_preferred:
                # Use first available Gemini model
                model_name = gemini_models[0]
            else:
                model_name = available_preferred[0]
            
            print(f"🤖 Using model: {model_name}")
            
            model = genai.GenerativeModel(model_name)
            
            # Test the connection
            print("🧪 Testing API connection...")
            test_response = model.generate_content("Say only the word 'SUCCESS'")
            
            test_result = test_response.text.strip()
            print(f"✅ API test successful! Response: '{test_result}'")
            
            return model
            
        except Exception as e:
            print(f"❌ Error in Gemini setup: {str(e)}")
            return None
    def enhanced_comprehensive_analysis(self, data, user_id):
        """Comprehensive analysis with Gemini fallback"""
        print(f"🎯 Starting comprehensive analysis for user: {user_id}")
        
        try:
            if self.use_llm and self.llm_client:
                print("🤖 Using Gemini analysis...")
                return self._gemini_analysis(data, user_id)
            else:
                print("🔄 Using rule-based analysis...")
                return self._rule_based_analysis(data, user_id)
                
        except Exception as e:
            print(f"❌ Analysis failed: {e}")
            return self._rule_based_analysis(data, user_id)
    
    def _gemini_analysis(self, data, user_id):
        """Gemini analysis with detailed input-focused prompt"""
        print("🧠 Using Gemini for comprehensive analysis...")
        
        assessment_data = data.get('assessment_data', {})
        prompt = self._build_detailed_analysis_prompt(assessment_data)
        
        try:
            # Enhanced prompt for detailed analysis without recommendations
            system_instruction = """You are a clinical stress analyst. Analyze the stress symptoms and provide detailed, input-driven analysis.

CRITICAL: DO NOT provide generic recommendations, advice, or coping strategies. Focus exclusively on analysis and explanation.

Return JSON with this exact structure:

{
    "stress_score": 7.5,
    "stress_level": "High",
    "detailed_analysis": "Detailed explanation connecting specific symptoms to overall stress level...",
    "symptom_breakdown": {
        "physical_impact": "Analysis of how physical symptoms contribute to stress",
        "emotional_impact": "Analysis of emotional state impact", 
        "cognitive_impact": "Analysis of cognitive symptoms effect",
        "lifestyle_impact": "Analysis of daily life disruptions"
    },
    "key_findings": ["Specific finding 1", "Specific finding 2", "Specific finding 3"],
    "score_explanation": "Detailed breakdown of how the numerical score was derived from inputs"
}

RULES:
- stress_score: number 1-10 (1=minimal stress, 10=extreme stress)
- stress_level: only: "Low", "Medium", "High", "Very High", or "Chronic High"
- Focus on connecting specific user inputs to outcomes
- Explain physiological and psychological impacts
- Describe symptom patterns and combinations
- Return ONLY valid JSON, no other text
- Be clinical and analytical, not prescriptive"""

            full_prompt = f"{system_instruction}\n\nAssessment Data:\n{prompt}"
            
            print("📤 Sending request to Gemini...")
            response = self.llm_client.generate_content(full_prompt)
            
            llm_response = response.text
            print("📨 Gemini response received")
            
            result = self._parse_detailed_gemini_response(llm_response, data, user_id)
            
            # Save to database if enabled
            if self.use_database and user_id and not user_id.startswith('temp_'):
                self.db_manager.save_stress_record(user_id, result)
            
            return result
            
        except Exception as e:
            print(f"❌ Gemini API call failed: {e}")
            return self._rule_based_analysis(data, user_id)
    
    def _build_detailed_analysis_prompt(self, assessment_data):
        """Build detailed analysis prompt focusing on input connections"""
        prompt_parts = ["COMPREHENSIVE STRESS ASSESSMENT DATA - Analyze and connect inputs to outcomes:"]
        
        # Physical symptoms with details
        physical = assessment_data.get('physicalSymptoms', [])
        if physical:
            symptoms = [s.get('symptom', '') for s in physical if s.get('symptom')]
            prompt_parts.append(f"PHYSICAL SYMPTOMS ({len(symptoms)}): {', '.join(symptoms)}")
        
        # Emotional state with details
        emotional = assessment_data.get('emotionalState', [])
        if emotional:
            emotions = [e.get('emotion', '') for e in emotional if e.get('emotion')]
            prompt_parts.append(f"EMOTIONAL STATE ({len(emotions)}): {', '.join(emotions)}")
        
        # Cognitive symptoms with details
        cognitive = assessment_data.get('cognitiveSymptoms', [])
        if cognitive:
            cognitives = [c.get('cognitive', '') for c in cognitive if c.get('cognitive')]
            prompt_parts.append(f"COGNITIVE SYMPTOMS ({len(cognitives)}): {', '.join(cognitives)}")
        
        # Lifestyle impact analysis
        lifestyle = assessment_data.get('lifestyleImpact', {})
        lifestyle_impacts = []
        for category, value in lifestyle.items():
            if value and value.get('value'):
                lifestyle_impacts.append(f"{category}: {value['value']} (weight: {value.get('weight', 0)})")
        if lifestyle_impacts:
            prompt_parts.append(f"LIFESTYLE IMPACT: {', '.join(lifestyle_impacts)}")
        
        # Coping mechanisms (note: these reduce stress)
        coping = assessment_data.get('copingMechanisms', [])
        if coping:
            coping_methods = [c.get('coping', '') for c in coping if c.get('coping')]
            if coping_methods:
                prompt_parts.append(f"COPING MECHANISMS ({len(coping_methods)}): {', '.join(coping_methods)}")
        
        # Duration analysis
        duration = assessment_data.get('duration')
        if duration and duration.get('duration'):
            prompt_parts.append(f"DURATION: {duration['duration']} (weight: {duration.get('weight', 0)})")
        
        # Stress source analysis
        stress_source = assessment_data.get('stressSource')
        if stress_source and stress_source.get('source'):
            prompt_parts.append(f"STRESS SOURCE: {stress_source['source']} (weight: {stress_source.get('weight', 0)})")
        
        # Initial mood context
        initial_mood = assessment_data.get('initialMood', {})
        if initial_mood.get('input_method'):
            mood_info = f"INITIAL MOOD: {initial_mood.get('input_method')}"
            if initial_mood.get('bubble_type'):
                mood_info += f" - {initial_mood['bubble_type']}"
            elif initial_mood.get('emoji'):
                mood_info += f" - {initial_mood['emoji']}"
            elif initial_mood.get('scene'):
                mood_info += f" - {initial_mood['scene']}"
            elif initial_mood.get('color'):
                mood_info += f" - {initial_mood['color']}"
            prompt_parts.append(mood_info)
        
        # Analysis instructions
        prompt_parts.extend([

            "",
            "=== CLINICAL ASSESSMENT TASK ===",
            "",
            "Analyze this stress profile using evidence-based clinical psychology principles.",
            "",
            "CALIBRATION REFERENCE - Use these as anchoring examples:",
            "",
            "Score 2.5 (LOW) - 'Normal Life Stress':",
            "Patient reports occasional headache, feels slightly worried about upcoming deadline.",
            "Sleep and appetite normal. Uses exercise to cope. Functioning well at work.",
            "Clinical assessment: Adaptive stress response, healthy coping, no intervention needed.",
            "",
            "Score 4.5 (MEDIUM) - 'Moderate Stress':",
            "Patient reports frequent headaches, tension in shoulders, feels anxious and irritable.",
            "Sleep is slightly disrupted (wakes once per night). Appetite slightly reduced.",
            "Has been ongoing for 3 weeks. Uses some coping (talks to friends).",
            "Clinical assessment: Stress is noticeable and affecting function, but manageable with support.",
            "",
            "Score 6.5 (HIGH) - 'Significant Stress':",
            "Patient reports constant tension, multiple physical symptoms (headaches, stomach issues, fatigue).",
            "Feels overwhelmed, anxious, having difficulty concentrating.",
            "Sleep moderately disrupted, appetite changes, withdrawing from social activities.",
            "Ongoing for 2 months. Limited coping mechanisms.",
            "Clinical assessment: Substantial functional impairment, professional support recommended.",
            "",
            "Score 8.5 (VERY HIGH) - 'Severe Stress':",
            "Patient reports severe physical symptoms across multiple systems, emotional dysregulation.",
            "Cannot sleep properly (4-5 hours, frequent waking), significant appetite changes.",
            "Difficulty performing at work, isolated from friends, feels hopeless.",
            "Chronic duration (3+ months). No effective coping strategies.",
            "Clinical assessment: Severe impairment requiring immediate intervention.",
            "",
            "YOUR ASSESSMENT APPROACH:",
            "",
            "1. Compare the patient's profile to these reference cases",
            "2. Consider:",
            "   - Symptom count AND severity (not just count)",
            "   - Functional impact (can they work? sleep? socialize?)",
            "   - Duration (recent vs chronic makes a difference)",
            "   - Protective factors (coping strategies, support systems)",
            "   - Lifestyle disruption (normal daily routines vs major disruption)",
            "",
            "3. Use the full 1-10 scale:",
            "   - 1.5-3.0 = LOW (manageable, minimal impairment, good coping)",
            "   - 3.5-5.5 = MEDIUM (noticeable stress, some impairment, needs support)",
            "   - 5.5-7.5 = HIGH (significant stress, clear impairment, needs intervention)",
            "   - 8.0-8.5 = VERY HIGH (severe stress, major impairment, urgent care)",
            "   - 8.5-10.0 = CHRONIC HIGH (crisis level, unable to function)",
            "",
            "4. Be nuanced:",
            "   - Someone with 2 mild symptoms + good sleep + active coping → LOW (2-3)",
            "   - Someone with 4 symptoms + some sleep issues + moderate coping → MEDIUM (4-5)",
            "   - Someone with many symptoms + major disruption + poor coping → HIGH (6-7)",
            "   - Reserve 8+ for truly severe, crisis-level presentations",
            "",
            "5. Consider context:",
            "   - Acute stress (< 1 week) with good coping → tends toward lower scores",
            "   - Chronic stress (months) with no coping → tends toward higher scores",
            "   - Effective coping mechanisms are protective (lower score)",
            "   - Major lifestyle disruption (can't work/sleep/function) → higher score",
            "",
            "CRITICAL: Most people fall in the 2.5-6.0 range. Scores above 7.0 should be reserved",
            "for severe cases with multiple symptoms, significant impairment, and poor coping.",
            "",
            "Do NOT provide recommendations, advice, or coping strategies - assessment only.",
            "",
            "Return ONLY this JSON:",
            "{",
            '  "stress_score": <1.0-10.0>,',
            '  "stress_level": "Low|Medium|High|Very High|Chronic High",',
            '  "detailed_analysis": "<clinical analysis comparing to reference cases>",',
            '  "symptom_breakdown": {',
            '    "physical_impact": "<analysis>",',
            '    "emotional_impact": "<analysis>",',
            '    "cognitive_impact": "<analysis>",',
            '    "lifestyle_impact": "<analysis>"',
            '  },',
            '  "key_findings": ["<finding>", "<finding>", "<finding>"],',
            '  "score_explanation": "<justify score by comparing to reference cases>"',
            "}"

        ])
        
        final_prompt = "\n".join(prompt_parts)
        
        print(f"📝 Detailed prompt built with {len(prompt_parts)} sections")
        return final_prompt
    
    def _parse_detailed_gemini_response(self, llm_response, data, user_id):
        """Parse Gemini response for detailed analysis"""
        try:
            # Clean response
            cleaned = llm_response.strip()
            
            # Extract JSON using regex
            json_match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if not json_match:
                print("❌ No JSON found in response, using rule-based fallback")
                return self._rule_based_analysis(data, user_id)
            
            json_str = json_match.group()
            llm_data = json.loads(json_str)
            
            # Validate and normalize score
            score = float(llm_data.get('stress_score', 5.0))
            score = max(1.0, min(10.0, score))
            
            # Validate and normalize level
            level = llm_data.get('stress_level', 'Medium')
            valid_levels = ['Low', 'Medium', 'High', 'Very High', 'Chronic High']
            if level not in valid_levels:
                level = self._categorize_stress(score)
            
            # Get detailed analysis components
            detailed_analysis = llm_data.get('detailed_analysis', 'Analysis completed based on your reported symptoms and their patterns.')
            symptom_breakdown = llm_data.get('symptom_breakdown', {})
            key_findings = llm_data.get('key_findings', [])
            score_explanation = llm_data.get('score_explanation', '')
            
            # If no key findings, generate from data
            if not key_findings:
                key_findings = self._generate_input_based_findings(data.get('assessment_data', {}))
            
            # Build comprehensive result
            result = {
                "stress_score": round(score, 1),
                "stress_level": level,
                "input_method": 'comprehensive_assessment',
                "detailed_analysis": detailed_analysis,
                "symptom_breakdown": symptom_breakdown,
                "key_findings": key_findings,
                "score_explanation": score_explanation,
                "timestamp": datetime.now().isoformat(),
                "analysis_metadata": {
                    "llm_used": True,
                    "model": "gemini-1.5-flash",
                    "symptoms_analyzed": self._count_total_symptoms(data.get('assessment_data', {})),
                    "analysis_type": "detailed_input_driven"
                }
            }
            
            print(f"✅ Detailed analysis complete: {score}/10 - {level}")
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Gemini JSON response: {e}")
            return self._rule_based_analysis(data, user_id)
        except Exception as e:
            print(f"❌ Error parsing Gemini response: {e}")
            return self._rule_based_analysis(data, user_id)

    def _count_total_symptoms(self, assessment_data):
        """Count total symptoms across all categories"""
        total = 0
        total += len(assessment_data.get('physicalSymptoms', []))
        total += len(assessment_data.get('emotionalState', []))
        total += len(assessment_data.get('cognitiveSymptoms', []))
        return total

    def _generate_input_based_findings(self, assessment_data):
        """Generate findings based on actual inputs"""
        findings = []
        
        # Physical symptoms analysis
        physical = assessment_data.get('physicalSymptoms', [])
        if physical:
            symptom_count = len(physical)
            findings.append(f"{symptom_count} physical symptom(s) indicating physiological stress response")
        
        # Emotional state analysis
        emotional = assessment_data.get('emotionalState', [])
        if emotional:
            emotion_count = len(emotional)
            findings.append(f"{emotion_count} emotional indicator(s) suggesting psychological impact")
        
        # Cognitive symptoms analysis
        cognitive = assessment_data.get('cognitiveSymptoms', [])
        if cognitive:
            cognitive_count = len(cognitive)
            findings.append(f"{cognitive_count} cognitive symptom(s) affecting thought processes")
        
        # Duration impact
        duration = assessment_data.get('duration')
        if duration and duration.get('duration'):
            findings.append(f"Stress duration: {duration['duration']} indicating persistence level")
        
        if not findings:
            findings = ["Multiple stress indicators detected across different domains"]
        
        return findings[:5]

    def _rule_based_analysis(self, data, user_id):
        """Rule-based analysis with detailed explanations"""
        print("🔄 Using rule-based analysis as fallback...")
        
        assessment_data = data.get('assessment_data', {})
        
        # Calculate score using rule-based system
        final_score = self._calculate_rule_based_score(assessment_data)
        stress_level = self._categorize_stress(final_score)
        
        # Generate detailed analysis
        detailed_analysis = self._generate_detailed_rule_based_explanation(final_score, stress_level, assessment_data)
        symptom_breakdown = self._generate_symptom_breakdown(assessment_data)
        key_findings = self._generate_input_based_findings(assessment_data)
        score_explanation = self._generate_score_explanation(final_score, assessment_data)
        
        result = {
            "stress_score": round(final_score, 1),
            "stress_level": stress_level,
            "input_method": 'comprehensive_assessment',
            "detailed_analysis": detailed_analysis,
            "symptom_breakdown": symptom_breakdown,
            "key_findings": key_findings,
            "score_explanation": score_explanation,
            "timestamp": datetime.now().isoformat(),
            "analysis_metadata": {
                "llm_used": False,
                "confidence": 0.7,
                "symptoms_analyzed": self._count_total_symptoms(assessment_data),
                "analysis_type": "rule_based_detailed"
            }
        }
        
        # Save to database if enabled
        if self.use_database and user_id and not user_id.startswith('temp_'):
            self.db_manager.save_stress_record(user_id, result)
        
        print(f"✅ Rule-based analysis complete: {final_score}/10 - {stress_level}")
        return result
    
    def _calculate_rule_based_score(self, assessment_data):
        """Calculate score using rule-based system"""
        base_score = 5.0
        
        # Physical symptoms
        physical_count = len(assessment_data.get('physicalSymptoms', []))
        base_score += min(physical_count * 0.4, 3.0)
        
        # Emotional symptoms
        emotional_count = len(assessment_data.get('emotionalState', []))
        base_score += min(emotional_count * 0.5, 4.0)
        
        # Cognitive symptoms
        cognitive_count = len(assessment_data.get('cognitiveSymptoms', []))
        base_score += min(cognitive_count * 0.3, 2.5)
        
        # Lifestyle impact
        lifestyle = assessment_data.get('lifestyleImpact', {})
        lifestyle_score = 0
        for category, value in lifestyle.items():
            if value and value.get('weight'):
                lifestyle_score += value['weight']
        base_score += min(lifestyle_score * 0.2, 2.0)
        
        # Coping mechanisms reduce stress
        coping_count = len(assessment_data.get('copingMechanisms', []))
        base_score -= min(coping_count * 0.4, 3.0)
        
        # Duration impact
        duration = assessment_data.get('duration')
        if duration and duration.get('weight'):
            base_score += duration['weight'] * 0.3
        
        # Stress source impact
        stress_source = assessment_data.get('stressSource')
        if stress_source and stress_source.get('weight'):
            base_score += stress_source['weight'] * 0.2
        
        return max(1.0, min(10.0, base_score))
    
    def _generate_detailed_rule_based_explanation(self, score, level, assessment_data):
        """Generate detailed explanation for rule-based analysis"""
        total_symptoms = self._count_total_symptoms(assessment_data)
        
        explanations = {
            'Low': f"With {total_symptoms} mild symptoms detected, your stress response is within manageable ranges. The symptom pattern suggests temporary situational stress rather than chronic issues.",
            'Medium': f"Your {total_symptoms} symptoms indicate moderate stress levels affecting multiple domains. The combination of physical and emotional indicators suggests your body's stress response is actively engaged.",
            'High': f"Significant stress load with {total_symptoms} symptoms across different systems. The symptom constellation indicates substantial physiological and psychological stress activation.",
            'Very High': f"High-intensity stress pattern with {total_symptoms} pronounced symptoms. The multi-system involvement suggests comprehensive stress response activation affecting daily functioning.",
            'Chronic High': f"Chronic stress configuration with {total_symptoms} persistent symptoms. The enduring pattern indicates sustained stress system activation requiring attention to physiological impacts."
        }
        
        return explanations.get(level, f"Analysis completed based on {total_symptoms} reported symptoms across physical, emotional, and cognitive domains.")
    
    def _generate_symptom_breakdown(self, assessment_data):
        """Generate symptom breakdown analysis"""
        breakdown = {
            "physical_impact": "No significant physical symptoms reported",
            "emotional_impact": "Emotional state within normal ranges", 
            "cognitive_impact": "Cognitive functioning appears unaffected",
            "lifestyle_impact": "Minimal disruption to daily activities"
        }
        
        # Physical symptoms analysis
        physical = assessment_data.get('physicalSymptoms', [])
        if physical:
            symptoms = [s.get('symptom', '') for s in physical if s.get('symptom')]
            breakdown["physical_impact"] = f"{len(symptoms)} physical symptoms indicating physiological stress response: {', '.join(symptoms)}"
        
        # Emotional state analysis
        emotional = assessment_data.get('emotionalState', [])
        if emotional:
            emotions = [e.get('emotion', '') for e in emotional if e.get('emotion')]
            breakdown["emotional_impact"] = f"{len(emotions)} emotional indicators: {', '.join(emotions)} affecting psychological state"
        
        # Cognitive symptoms analysis
        cognitive = assessment_data.get('cognitiveSymptoms', [])
        if cognitive:
            cognitives = [c.get('cognitive', '') for c in cognitive if c.get('cognitive')]
            breakdown["cognitive_impact"] = f"{len(cognitives)} cognitive symptoms: {', '.join(cognitives)} affecting mental processes"
        
        # Lifestyle impact analysis
        lifestyle = assessment_data.get('lifestyleImpact', {})
        lifestyle_items = []
        for category, value in lifestyle.items():
            if value and value.get('value'):
                lifestyle_items.append(f"{category}: {value['value']}")
        if lifestyle_items:
            breakdown["lifestyle_impact"] = f"Lifestyle disruptions detected: {', '.join(lifestyle_items)}"
        
        return breakdown
    
    def _generate_score_explanation(self, score, assessment_data):
        """Generate explanation of how score was derived"""
        components = []
        
        physical_count = len(assessment_data.get('physicalSymptoms', []))
        if physical_count > 0:
            components.append(f"{physical_count} physical symptoms")
        
        emotional_count = len(assessment_data.get('emotionalState', []))
        if emotional_count > 0:
            components.append(f"{emotional_count} emotional indicators")
        
        cognitive_count = len(assessment_data.get('cognitiveSymptoms', []))
        if cognitive_count > 0:
            components.append(f"{cognitive_count} cognitive symptoms")
        
        duration = assessment_data.get('duration')
        if duration and duration.get('weight', 0) > 0:
            components.append(f"duration: {duration['duration']}")
        
        if components:
            return f"Score derived from: {', '.join(components)}. Base moderate stress (5.0) adjusted based on symptom severity and duration."
        else:
            return "Score based on baseline moderate stress assessment with minimal symptom reporting."
    
    def _categorize_stress(self, score):
        """Categorize stress level based on score"""
        if score <= 3.0:
            return "Low"
        elif score <= 5.0:
            return "Medium"
        elif score <= 7.0:
            return "High"
        elif score <= 8.5:
            return "Very High"
        else:
            return "Chronic High"
    
    def get_user_trend(self, user_id):
        """Get user stress trend"""
        if not self.use_database:
            return "no_data"
            
        try:
            history = self.db_manager.get_user_history(user_id, 5)
            
            if len(history) < 2:
                return "insufficient_data"
            
            # Extract recent scores
            scores = []
            for record in history[:3]:
                try:
                    score = float(record.get('stress_score', 5))
                    scores.append(score)
                except (ValueError, TypeError):
                    continue
            
            if len(scores) < 2:
                return "stable"
            
            # Calculate trend (most recent first)
            recent_avg = sum(scores[:2]) / 2
            previous_avg = sum(scores[2:]) / len(scores[2:]) if len(scores) > 2 else scores[-1]
            
            trend_diff = recent_avg - previous_avg
            
            if trend_diff > 0.3:
                return "increasing"
            elif trend_diff < -0.3:
                return "decreasing"
            else:
                return "stable"
                
        except Exception as e:
            print(f"❌ Error calculating trend: {e}")
            return "unknown"
        