import React from 'react';
import { Button } from '@mui/material';
import { GitHubIcon, SlackIcon, JiraIcon } from './icons.tsx';

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
  onOpenGithubModal, 
  onOpenSlackModal, 
  onOpenJiraModal 
}) => {
  return (
    <div className="p-8">
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
          </div>
          <p className="text-gray-600 mb-4">
            Connect your GitHub account to access repositories and perform operations.
          </p>
          <Button 
            variant="contained" 
            color="primary"
            onClick={onOpenGithubModal}
            startIcon={<GitHubIcon size={20} currentColor="#fff" />}
          >
            Configure GitHub
          </Button>
        </div>

        {/* Slack Settings */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center mb-4">
            <SlackIcon size={24} currentColor="#4A154B" />
            <h3 className="text-xl font-semibold ml-2">Slack Integration</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Connect your Slack workspace to send notifications and interact with channels.
          </p>
          <Button 
            variant="contained" 
            color="primary"
            onClick={onOpenSlackModal}
            startIcon={<SlackIcon size={20} currentColor="#fff" />}
          >
            Configure Slack
          </Button>
        </div>

        {/* Jira Settings */}
        <div className="bg-white p-6 rounded-lg shadow-md">
          <div className="flex items-center mb-4">
            <JiraIcon size={24} currentColor="#0052CC" />
            <h3 className="text-xl font-semibold ml-2">Jira Integration</h3>
          </div>
          <p className="text-gray-600 mb-4">
            Connect your Jira instance to access and manage projects and issues.
          </p>
          <Button 
            variant="contained" 
            color="primary"
            onClick={onOpenJiraModal}
            startIcon={<JiraIcon size={20} currentColor="#fff" />}
          >
            Configure Jira
          </Button>
        </div>
      </div>
    </div>
  );
};

export default SettingsPanel; 