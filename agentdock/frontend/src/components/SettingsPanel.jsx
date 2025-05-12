import React, { useState, useEffect } from 'react';
import { Button } from '@mui/material';
import { GitHubIcon, SlackIcon, JiraIcon } from './icons.tsx';
import GitHubTokenModal from "./GitHubTokenModal";
import SlackTokenModal from "./SlackTokenModal";
import JiraTokenModal from "./JiraTokenModal";

// LocalStorage keys
const GH_CONFIG_STATUS_KEY = 'github_config_status';
const SLACK_CONFIG_STATUS_KEY = 'slack_config_status';
const JIRA_CONFIG_STATUS_KEY = 'jira_config_status';

/**
 * A reusable component for integration settings
 * 
 * @param {Object} props - Component props
 * @param {Function} props.onBackToChat - Function to call to go back to chat
 * @param {Function} props.onOpenGithubModal - Function to call to open the GitHub modal
 * @param {Function} props.onOpenSlackModal - Function to call to open the Slack modal
 * @param {Function} props.onOpenJiraModal - Function to call to open the Jira modal
 * @returns {JSX.Element} The SettingsPanel component
 */
const SettingsPanel = ({ 
  onBackToChat,
}) => {
  const [githubStatus, setGithubStatus] = useState('');
  const [slackStatus, setSlackStatus] = useState('');
  const [jiraStatus, setJiraStatus] = useState('');
  
  // Integration configuration modals
  const [openGithubModal, setOpenGithubModal] = useState(false);
  const [openSlackModal, setOpenSlackModal] = useState(false);
  const [openJiraModal, setOpenJiraModal] = useState(false);

  const onClose = () => {
    const loadedGithubStatus = localStorage.getItem(GH_CONFIG_STATUS_KEY) || '';
    const loadedSlackStatus = localStorage.getItem(SLACK_CONFIG_STATUS_KEY) || '';
    const loadedJiraStatus = localStorage.getItem(JIRA_CONFIG_STATUS_KEY) || '';
    
    setGithubStatus(loadedGithubStatus);
    setSlackStatus(loadedSlackStatus);
    setJiraStatus(loadedJiraStatus);
  }

  useEffect(() => {
    onClose();
  }, []);

  const isConfigured = (status) => {
    return status && !status.includes('failed');
  };

  return (
    <div className="p-8">
      {/* Configuration Modals */}
      <GitHubTokenModal 
        open={openGithubModal} 
        onClose={() => {
          setOpenGithubModal(false);
          onClose();
        }} 
      />
      <SlackTokenModal 
        open={openSlackModal} 
        onClose={() => {
          setOpenSlackModal(false);
          onClose();
        }} 
      />
      <JiraTokenModal 
        open={openJiraModal} 
        onClose={() => {
          setOpenJiraModal(false);
          onClose();
        }} 
      />
      <div className="mb-8 mt-2 flex items-center justify-between">
        <h2 className="text-2xl font-bold text-gray-800">Integration Settings</h2>
        <button 
          className="text-blue-600 hover:text-blue-800 flex items-center"
          onClick={onBackToChat}
        >
          <span>Back to Chat</span>
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* GitHub Settings */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center mb-4">
            <GitHubIcon size={24} currentColor="#333" />
            <h3 className="text-xl font-semibold ml-2">GitHub Integration</h3>
            {isConfigured(githubStatus) && (
              <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                Configured
              </span>
            )}
          </div>
          <p className="text-gray-600 mb-4">
            Connect your GitHub account to access repositories and perform operations.
          </p>
          {githubStatus && (
            <p className={`text-sm mb-4 ${githubStatus.includes('failed') ? 'text-red-600' : 'text-green-600'}`}>
              {githubStatus}
            </p>
          )}
          <Button 
            variant="contained" 
            color="primary"
            onClick={() => {
              setOpenGithubModal(true);
            }}
            startIcon={<GitHubIcon size={20} currentColor="#fff" />}
          >
            {isConfigured(githubStatus) ? 'Update GitHub Configuration' : 'Configure GitHub'}
          </Button>
        </div>

        {/* Slack Settings */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center mb-4">
            <SlackIcon size={24} currentColor="#4A154B" />
            <h3 className="text-xl font-semibold ml-2">Slack Integration</h3>
            {isConfigured(slackStatus) && (
              <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                Configured
              </span>
            )}
          </div>
          <p className="text-gray-600 mb-4">
            Connect your Slack workspace to send notifications and interact with channels.
          </p>
          {slackStatus && (
            <p className={`text-sm mb-4 ${slackStatus.includes('failed') ? 'text-red-600' : 'text-green-600'}`}>
              {slackStatus}
            </p>
          )}
          <Button 
            variant="contained" 
            color="primary"
            onClick={() => {
              setOpenSlackModal(true);
            }}
            startIcon={<SlackIcon size={20} currentColor="#fff" />}
          >
            {isConfigured(slackStatus) ? 'Update Slack Configuration' : 'Configure Slack'}
          </Button>
        </div>

        {/* Jira Settings */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center mb-4">
            <JiraIcon size={24} currentColor="#0052CC" />
            <h3 className="text-xl font-semibold ml-2">Jira Integration</h3>
            {isConfigured(jiraStatus) && (
              <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                Configured
              </span>
            )}
          </div>
          <p className="text-gray-600 mb-4">
            Connect your Jira instance to access and manage projects and issues.
          </p>
          {jiraStatus && (
            <p className={`text-sm mb-4 ${jiraStatus.includes('failed') ? 'text-red-600' : 'text-green-600'}`}>
              {jiraStatus}
            </p>
          )}
          <Button 
            variant="contained" 
            color="primary"
            onClick={() => {
              setOpenJiraModal(true);
            }}
            startIcon={<JiraIcon size={20} currentColor="#fff" />}
          >
            {isConfigured(jiraStatus) ? 'Update Jira Configuration' : 'Configure Jira'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel; 