import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from typing import List, Dict, Any
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobScraper:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def calculate_match_percentage(self, job_title: str, job_description: str, user_skills: List[str]) -> float:
        """Calculate how well a job matches the user's skills"""
        # Convert everything to lowercase for comparison
        job_text = (job_title + " " + job_description).lower()
        user_skills = [skill.lower() for skill in user_skills]
        
        # Count matches
        matches = sum(1 for skill in user_skills if skill in job_text)
        
        # Calculate percentage (minimum 50% if at least one skill matches)
        if matches > 0:
            return max(50, (matches / len(user_skills)) * 100)
        return 0

    def search_naukri(self, keywords: str, location: str) -> List[Dict[str, Any]]:
        """Search for jobs on Naukri.com"""
        try:
            # Format the search URL
            search_url = f"https://www.naukri.com/{keywords.replace(' ', '-')}-jobs-in-{location.replace(' ', '-')}"
            logger.info(f"Searching Naukri with URL: {search_url}")
            
            response = self.session.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = []
            
            # Find job listings
            job_elements = soup.find_all('article', class_='jobTuple')
            
            for job in job_elements[:10]:  # Limit to 10 results
                try:
                    title = job.find('a', class_='title').text.strip()
                    company = job.find('a', class_='subTitle').text.strip()
                    location = job.find('span', class_='location').text.strip()
                    link = job.find('a', class_='title')['href']
                    
                    # Get job description
                    desc_response = self.session.get(link)
                    desc_soup = BeautifulSoup(desc_response.text, 'html.parser')
                    description = desc_soup.find('div', class_='job-description').text.strip()
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'link': link,
                        'description': description,
                        'source': 'Naukri'
                    })
                except Exception as e:
                    logger.error(f"Error parsing job listing: {e}")
                    continue
                    
            return jobs
        except Exception as e:
            logger.error(f"Error searching Naukri: {e}")
            return []

    def search_linkedin(self, keywords: str, location: str) -> List[Dict[str, Any]]:
        """Search for jobs on LinkedIn"""
        try:
            # Format the search URL
            search_url = f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}&location={location.replace(' ', '%20')}"
            logger.info(f"Searching LinkedIn with URL: {search_url}")
            
            response = self.session.get(search_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            jobs = []
            
            # Find job listings
            job_elements = soup.find_all('div', class_='base-card')
            
            for job in job_elements[:10]:  # Limit to 10 results
                try:
                    title = job.find('h3', class_='base-search-card__title').text.strip()
                    company = job.find('h4', class_='base-search-card__subtitle').text.strip()
                    location = job.find('span', class_='job-search-card__location').text.strip()
                    link = job.find('a', class_='base-card__full-link')['href']
                    
                    # Get job description
                    desc_response = self.session.get(link)
                    desc_soup = BeautifulSoup(desc_response.text, 'html.parser')
                    description = desc_soup.find('div', class_='description__text').text.strip()
                    
                    jobs.append({
                        'title': title,
                        'company': company,
                        'location': location,
                        'link': link,
                        'description': description,
                        'source': 'LinkedIn'
                    })
                except Exception as e:
                    logger.error(f"Error parsing LinkedIn job listing: {e}")
                    continue
                    
            return jobs
        except Exception as e:
            logger.error(f"Error searching LinkedIn: {e}")
            return []

    def search_jobs(self, keywords: str, location: str) -> List[Dict[str, Any]]:
        """Search for jobs across multiple platforms"""
        all_jobs = []
        
        # Split keywords into individual skills
        user_skills = [k.strip() for k in keywords.split(',')]
        
        # Search Naukri
        naukri_jobs = self.search_naukri(keywords, location)
        all_jobs.extend(naukri_jobs)
        
        # Search LinkedIn
        linkedin_jobs = self.search_linkedin(keywords, location)
        all_jobs.extend(linkedin_jobs)
        
        # Calculate match percentage for each job
        for job in all_jobs:
            match_percentage = self.calculate_match_percentage(
                job['title'],
                job['description'],
                user_skills
            )
            job['match_percentage'] = match_percentage
        
        # Sort jobs by match percentage (highest first)
        all_jobs.sort(key=lambda x: x['match_percentage'], reverse=True)
        
        # Return only jobs with at least 50% match
        return [job for job in all_jobs if job['match_percentage'] >= 50]

    def close(self):
        """Close the session"""
        self.session.close()
        
    def __del__(self):
        """Destructor to ensure session is closed"""
        self.close() 