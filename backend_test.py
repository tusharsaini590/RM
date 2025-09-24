#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Knowledge Aggregator
Tests all API endpoints and AI integration functionality
"""

import requests
import json
import time
import uuid
from datetime import datetime
import sys

# Backend URL from environment
BACKEND_URL = "https://factfirst.preview.emergentagent.com/api"

class KnowledgeAggregatorTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.test_data = {}
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                data = response.json()
                if "message" in data:
                    self.log_test("Root Endpoint", True, "API root accessible")
                    return True
                else:
                    self.log_test("Root Endpoint", False, "Invalid response format", data)
                    return False
            else:
                self.log_test("Root Endpoint", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Root Endpoint", False, "Connection failed", str(e))
            return False
    
    def test_setup_default_sources(self):
        """Test setting up default RSS sources"""
        try:
            response = self.session.post(f"{BACKEND_URL}/setup/default-sources")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    self.log_test("Default RSS Sources Setup", True, "Default sources configured")
                    return True
                else:
                    self.log_test("Default RSS Sources Setup", False, "Setup failed", data)
                    return False
            else:
                self.log_test("Default RSS Sources Setup", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Default RSS Sources Setup", False, "Request failed", str(e))
            return False
    
    def test_get_rss_sources(self):
        """Test getting RSS sources"""
        try:
            response = self.session.get(f"{BACKEND_URL}/rss-sources")
            if response.status_code == 200:
                sources = response.json()
                if isinstance(sources, list) and len(sources) > 0:
                    self.log_test("Get RSS Sources", True, f"Retrieved {len(sources)} RSS sources")
                    self.test_data['rss_sources'] = sources
                    return True
                else:
                    self.log_test("Get RSS Sources", False, "No RSS sources found", sources)
                    return False
            else:
                self.log_test("Get RSS Sources", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Get RSS Sources", False, "Request failed", str(e))
            return False
    
    def test_add_rss_source(self):
        """Test adding a new RSS source"""
        try:
            test_source = {
                "name": "Test Tech News",
                "url": "https://feeds.feedburner.com/oreilly/radar",
                "enabled": True,
                "reputation_score": 7.0,
                "fetch_frequency": 30
            }
            
            response = self.session.post(f"{BACKEND_URL}/rss-sources", json=test_source)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and "source_id" in data:
                    self.log_test("Add RSS Source", True, "RSS source added successfully")
                    self.test_data['test_source_id'] = data['source_id']
                    return True
                else:
                    self.log_test("Add RSS Source", False, "Invalid response", data)
                    return False
            else:
                self.log_test("Add RSS Source", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Add RSS Source", False, "Request failed", str(e))
            return False
    
    def test_fetch_rss_content(self):
        """Test fetching content from RSS source"""
        if 'rss_sources' not in self.test_data or not self.test_data['rss_sources']:
            self.log_test("Fetch RSS Content", False, "No RSS sources available for testing")
            return False
        
        try:
            # Use the first available RSS source
            source = self.test_data['rss_sources'][0]
            source_id = source['id']
            
            response = self.session.post(f"{BACKEND_URL}/rss-sources/{source_id}/fetch")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success":
                    processed_count = data.get("processed_count", 0)
                    self.log_test("Fetch RSS Content", True, f"Processed {processed_count} articles from RSS feed")
                    return True
                else:
                    self.log_test("Fetch RSS Content", False, "Fetch failed", data)
                    return False
            else:
                self.log_test("Fetch RSS Content", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Fetch RSS Content", False, "Request failed", str(e))
            return False
    
    def test_ai_content_analysis(self):
        """Test AI content analysis endpoint"""
        try:
            test_content = {
                "title": "Breakthrough in Quantum Computing: New Algorithm Achieves 99% Error Correction",
                "content": "Researchers at MIT have developed a revolutionary quantum error correction algorithm that achieves unprecedented 99% accuracy in maintaining quantum states. This breakthrough addresses one of the most significant challenges in quantum computing - quantum decoherence. The new algorithm uses machine learning techniques to predict and correct quantum errors in real-time, potentially accelerating the development of practical quantum computers by decades. The research team demonstrated the algorithm on a 50-qubit quantum processor, showing stable computation for over 10 minutes - a record in the field. This advancement could revolutionize cryptography, drug discovery, and complex optimization problems.",
                "source": "MIT Technology Review"
            }
            
            response = self.session.post(f"{BACKEND_URL}/content/analyze", json=test_content)
            if response.status_code == 200:
                analysis = response.json()
                
                # Check if all required fields are present
                required_fields = ['knowledge_density_score', 'credibility_score', 'distraction_score', 'summary']
                missing_fields = [field for field in required_fields if field not in analysis]
                
                if missing_fields:
                    self.log_test("AI Content Analysis", False, f"Missing fields: {missing_fields}", analysis)
                    return False
                
                # Validate score ranges (0-10)
                scores = {
                    'knowledge_density_score': analysis.get('knowledge_density_score'),
                    'credibility_score': analysis.get('credibility_score'),
                    'distraction_score': analysis.get('distraction_score')
                }
                
                invalid_scores = []
                for score_name, score_value in scores.items():
                    if not isinstance(score_value, (int, float)) or score_value < 0 or score_value > 10:
                        invalid_scores.append(f"{score_name}: {score_value}")
                
                if invalid_scores:
                    self.log_test("AI Content Analysis", False, f"Invalid scores: {invalid_scores}", analysis)
                    return False
                
                # Calculate cognitive utility
                cognitive_utility = scores['knowledge_density_score'] + scores['credibility_score'] - scores['distraction_score']
                
                self.log_test("AI Content Analysis", True, 
                             f"AI analysis successful - Knowledge: {scores['knowledge_density_score']}, "
                             f"Credibility: {scores['credibility_score']}, Distraction: {scores['distraction_score']}, "
                             f"Cognitive Utility: {cognitive_utility:.1f}")
                
                self.test_data['ai_analysis'] = analysis
                return True
            else:
                self.log_test("AI Content Analysis", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("AI Content Analysis", False, "Request failed", str(e))
            return False
    
    def test_manual_content_upload(self):
        """Test manual content upload with AI analysis"""
        try:
            test_upload = {
                "title": "The Future of Renewable Energy Storage Solutions",
                "content": "As renewable energy sources like solar and wind become more prevalent, the challenge of energy storage has become critical. New battery technologies, including solid-state batteries and flow batteries, are showing promise for large-scale energy storage. These technologies could enable 24/7 renewable energy supply, making fossil fuels obsolete for electricity generation. Recent advances in lithium-sulfur batteries have achieved energy densities 5 times higher than traditional lithium-ion batteries, while new sodium-ion batteries offer a more sustainable alternative using abundant materials.",
                "source": "Manual Upload - Energy Research"
            }
            
            response = self.session.post(f"{BACKEND_URL}/content/manual", json=test_upload)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and "content_id" in data:
                    self.log_test("Manual Content Upload", True, "Content uploaded and analyzed successfully")
                    self.test_data['uploaded_content_id'] = data['content_id']
                    return True
                else:
                    self.log_test("Manual Content Upload", False, "Upload failed", data)
                    return False
            else:
                self.log_test("Manual Content Upload", False, f"HTTP {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Manual Content Upload", False, "Request failed", str(e))
            return False
    
    def test_get_content_feed(self):
        """Test getting content feed with various filters"""
        try:
            # Test basic content retrieval
            response = self.session.get(f"{BACKEND_URL}/content?limit=10")
            if response.status_code == 200:
                content = response.json()
                if isinstance(content, list):
                    self.log_test("Get Content Feed - Basic", True, f"Retrieved {len(content)} content items")
                    
                    # Verify content structure
                    if content:
                        first_item = content[0]
                        required_fields = ['id', 'title', 'content', 'source', 'cognitive_utility_score']
                        missing_fields = [field for field in required_fields if field not in first_item]
                        
                        if missing_fields:
                            self.log_test("Content Structure Validation", False, f"Missing fields: {missing_fields}")
                            return False
                        else:
                            self.log_test("Content Structure Validation", True, "Content items have required fields")
                    
                    self.test_data['content_items'] = content
                else:
                    self.log_test("Get Content Feed - Basic", False, "Invalid response format", content)
                    return False
            else:
                self.log_test("Get Content Feed - Basic", False, f"HTTP {response.status_code}", response.text)
                return False
            
            # Test with minimum score filter
            response = self.session.get(f"{BACKEND_URL}/content?limit=5&min_score=5.0")
            if response.status_code == 200:
                filtered_content = response.json()
                self.log_test("Get Content Feed - Min Score Filter", True, f"Retrieved {len(filtered_content)} items with min_score=5.0")
            else:
                self.log_test("Get Content Feed - Min Score Filter", False, f"HTTP {response.status_code}")
                return False
            
            # Test with serendipity mode
            response = self.session.get(f"{BACKEND_URL}/content?limit=5&serendipity=true")
            if response.status_code == 200:
                serendipity_content = response.json()
                self.log_test("Get Content Feed - Serendipity Mode", True, f"Retrieved {len(serendipity_content)} items with serendipity")
            else:
                self.log_test("Get Content Feed - Serendipity Mode", False, f"HTTP {response.status_code}")
                return False
            
            return True
            
        except Exception as e:
            self.log_test("Get Content Feed", False, "Request failed", str(e))
            return False
    
    def test_user_feedback_system(self):
        """Test user feedback logging"""
        if 'content_items' not in self.test_data or not self.test_data['content_items']:
            self.log_test("User Feedback System", False, "No content items available for feedback testing")
            return False
        
        try:
            content_id = self.test_data['content_items'][0]['id']
            
            # Test different feedback actions
            feedback_actions = ['expand', 'helpful', 'unhelpful', 'flag']
            
            for action in feedback_actions:
                feedback = {
                    "content_id": content_id,
                    "action": action
                }
                
                response = self.session.post(f"{BACKEND_URL}/feedback", json=feedback)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        self.log_test(f"User Feedback - {action}", True, f"Feedback '{action}' logged successfully")
                    else:
                        self.log_test(f"User Feedback - {action}", False, "Feedback logging failed", data)
                        return False
                else:
                    self.log_test(f"User Feedback - {action}", False, f"HTTP {response.status_code}", response.text)
                    return False
            
            return True
            
        except Exception as e:
            self.log_test("User Feedback System", False, "Request failed", str(e))
            return False
    
    def test_cognitive_utility_scoring(self):
        """Test cognitive utility score calculation"""
        if 'content_items' not in self.test_data or not self.test_data['content_items']:
            self.log_test("Cognitive Utility Scoring", False, "No content items available for scoring validation")
            return False
        
        try:
            valid_scores = 0
            total_items = len(self.test_data['content_items'])
            
            for item in self.test_data['content_items']:
                knowledge = item.get('knowledge_density_score', 0)
                credibility = item.get('credibility_score', 0)
                distraction = item.get('distraction_score', 0)
                cognitive_utility = item.get('cognitive_utility_score', 0)
                
                # Verify cognitive utility calculation: knowledge + credibility - distraction
                expected_score = max(0, knowledge + credibility - distraction)
                
                if abs(cognitive_utility - expected_score) < 0.1:  # Allow small floating point differences
                    valid_scores += 1
                else:
                    self.log_test("Cognitive Utility Scoring", False, 
                                 f"Score mismatch for item '{item['title'][:50]}...': "
                                 f"Expected {expected_score:.1f}, Got {cognitive_utility:.1f}")
                    return False
            
            if valid_scores == total_items:
                self.log_test("Cognitive Utility Scoring", True, 
                             f"All {total_items} items have correct cognitive utility scores")
                return True
            else:
                self.log_test("Cognitive Utility Scoring", False, 
                             f"Only {valid_scores}/{total_items} items have correct scores")
                return False
                
        except Exception as e:
            self.log_test("Cognitive Utility Scoring", False, "Validation failed", str(e))
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Knowledge Aggregator Backend Tests")
        print("=" * 60)
        
        # Test sequence
        tests = [
            self.test_root_endpoint,
            self.test_setup_default_sources,
            self.test_get_rss_sources,
            self.test_add_rss_source,
            self.test_fetch_rss_content,
            self.test_ai_content_analysis,
            self.test_manual_content_upload,
            self.test_get_content_feed,
            self.test_user_feedback_system,
            self.test_cognitive_utility_scoring
        ]
        
        passed = 0
        failed = 0
        
        for test in tests:
            try:
                if test():
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                print(f"❌ CRITICAL ERROR in {test.__name__}: {str(e)}")
                failed += 1
            
            # Small delay between tests
            time.sleep(0.5)
        
        print("\n" + "=" * 60)
        print(f"📊 TEST SUMMARY: {passed} passed, {failed} failed")
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Backend is working correctly.")
        else:
            print(f"⚠️  {failed} tests failed. Check the details above.")
        
        return failed == 0

def main():
    """Main test execution"""
    tester = KnowledgeAggregatorTester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()