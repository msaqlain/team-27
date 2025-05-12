// This file handles communication with the backend API for chat functionality
import config from "../../config.js";

/**
 * DoChat sends a message to the backend API and returns a stream of the response
 * @param {string} message - The user's message
 * @param {Array} chatHistory - Optional chat history (last few messages)
 * @returns {AsyncGenerator} - A stream of response chunks
 */
export async function* DoChat(message, chatHistory = []) {
  try {
    // Prepare the request payload
    const payload = {
      message: message,
      context: {
        chat_history: chatHistory,
      },
    };

    // Call the backend API endpoint
    const response = await fetch(
      `${config.API_BASE_URL}${config.ENDPOINTS.CHAT}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      }
    );

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    // Parse the JSON response
    const data = await response.json();
    // Get the assistant's response
    const assistantResponse = data.response;

    // If we have action_taken data, we can format it nicely
    if (data.action_taken) {
      const chunks = assistantResponse.split(" ");
      let accumulatedText = "";

      for (const word of chunks) {
        accumulatedText += word + " ";
        yield accumulatedText;
        await new Promise((resolve) => setTimeout(resolve, 10));
      }

      // Handle formatted result if exists
      if (data.action_taken.result) {
        let formattedResult = "";

        switch (data.action_taken.action) {
          case "list_prs":
            formattedResult = formatPullRequests(data.action_taken.result);
            break;
          case "get_pr_summary":
            formattedResult = formatPRSummary(data.action_taken.result);
            break;
          case "get_repo_info":
          case "get_stats":
            formattedResult = formatRepoInfo(data.action_taken.result);
            break;
          case "list_my_repos":
            formattedResult = formatRepositories(data.action_taken.result);
            break;
          case "create_ticket":
            formattedResult = formatJiraTicketCreation(data.action_taken);
            break;
          case "update_status":
            formattedResult = formatJiraTicketStatusUpdate(data.action_taken);
            break;
          case "get_details":
            formattedResult = formatJiraTicketDetails(
              data.action_taken.details
            );
            break;
          case "send_message":
            yield "";
            break;
          case "cross_platform":
            yield "";
            break;
          default:
            formattedResult = JSON.stringify(data.action_taken.result, null, 2);
        }

        if (formattedResult) {
          yield accumulatedText + "\n\n" + formattedResult;
        }
      }
    } else {
      yield assistantResponse;
    }
  } catch (error) {
    console.error("Error in DoChat:", error);
    yield `Error: ${error.message}`;
  }
}

// Helper functions to format GitHub API responses
function formatPullRequests(prs) {
  if (!prs || prs.length === 0) {
    return "No pull requests found.";
  }

  return prs
    .map(
      (pr) =>
        `**PR #${pr.number}**: ${pr.title}\n` +
        `Status: ${pr.state} | Created: ${new Date(
          pr.created_at
        ).toLocaleDateString()}\n` +
        `Author: ${pr.user.login} | URL: ${pr.html_url}`
    )
    .join("\n\n");
}

function formatPRSummary(pr) {
  if (!pr) {
    return "Pull request details not found.";
  }

  return (
    `**Title**: ${pr.title}\n` +
    `**Status**: ${pr.state} ${pr.merged ? "(Merged)" : ""}\n` +
    `**Author**: ${pr.user.login}\n` +
    `**Created**: ${new Date(pr.created_at).toLocaleDateString()}\n` +
    `**Description**: ${pr.body || "No description provided"}\n` +
    `**Commits**: ${pr.commits} | **Additions**: ${pr.additions} | **Deletions**: ${pr.deletions}\n` +
    `**URL**: ${pr.html_url}`
  );
}

function formatRepoInfo(repo) {
  if (!repo) {
    return "Repository information not found.";
  }

  return (
    `**Repository**: ${repo.full_name}\n` +
    `**Description**: ${repo.description || "No description"}\n` +
    `**Stars**: ${repo.stargazers_count} | **Forks**: ${repo.forks_count} | **Watchers**: ${repo.watchers_count}\n` +
    `**Language**: ${repo.language || "Not specified"}\n` +
    `**Created**: ${new Date(
      repo.created_at
    ).toLocaleDateString()} | **Last Updated**: ${new Date(
      repo.updated_at
    ).toLocaleDateString()}\n` +
    `**License**: ${repo.license ? repo.license.name : "No license"}\n` +
    `**Issues**: ${repo.open_issues_count} open issues\n` +
    `**URL**: ${repo.html_url}`
  );
}

function formatRepositories(repos) {
  if (!repos || repos.length === 0) {
    return "No repositories found.";
  }

  return repos
    .map(
      (repo) =>
        `**${repo.name}** (${repo.private ? "Private" : "Public"})\n` +
        `Description: ${repo.description || "No description"}\n` +
        `Stars: ${repo.stars} | Forks: ${repo.forks}\n` +
        `URL: ${repo.url}`
    )
    .join("\n\n");
}

// New helper functions for Jira responses
function formatJiraTicketCreation(actionData) {
  if (!actionData || !actionData.details) {
    return "Ticket creation details not available.";
  }

  return (
    `**Jira Ticket Created**\n` +
    `**Key**: ${actionData.ticket_key}\n` +
    `**Summary**: ${actionData.details.summary}\n` +
    `**Type**: ${actionData.details.issue_type}\n` +
    `**Description**: ${actionData.details.description || "No description"}`
  );
}

function formatJiraTicketStatusUpdate(actionData) {
  if (!actionData) {
    return "Ticket status update details not available.";
  }

  return (
    `**Jira Ticket Status Updated**\n` +
    `**Ticket**: ${actionData.ticket_key}\n` +
    `**New Status**: ${actionData.new_status}`
  );
}

function formatJiraTicketDetails(details) {
  if (!details) {
    return "Ticket details not available.";
  }

  return (
    `**Jira Ticket Details**\n` +
    `**Key**: ${details.key}\n` +
    `**Summary**: ${details.summary}\n` +
    `**Status**: ${details.status}\n` +
    `**Assignee**: ${details.assignee}\n` +
    `**Description**: ${details.description || "No description"}`
  );
}
