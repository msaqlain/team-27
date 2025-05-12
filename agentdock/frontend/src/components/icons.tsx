import React from "react";

export const SparklesIcon = ({ size = 16 }: { size?: number }) => (
  <svg
    height={size}
    strokeLinejoin="round"
    viewBox="0 0 16 16"
    width={size}
    style={{ color: 'currentcolor' }}
  >
    <path
      d="M2.5 0.5V0H3.5V0.5C3.5 1.60457 4.39543 2.5 5.5 2.5H6V3V3.5H5.5C4.39543 3.5 3.5 4.39543 3.5 5.5V6H3H2.5V5.5C2.5 4.39543 1.60457 3.5 0.5 3.5H0V3V2.5H0.5C1.60457 2.5 2.5 1.60457 2.5 0.5Z"
      fill="currentColor"
    />
    <path
      d="M14.5 4.5V5H13.5V4.5C13.5 3.94772 13.0523 3.5 12.5 3.5H12V3V2.5H12.5C13.0523 2.5 13.5 2.05228 13.5 1.5V1H14H14.5V1.5C14.5 2.05228 14.9477 2.5 15.5 2.5H16V3V3.5H15.5C14.9477 3.5 14.5 3.94772 14.5 4.5Z"
      fill="currentColor"
    />
    <path
      d="M8.40706 4.92939L8.5 4H9.5L9.59294 4.92939C9.82973 7.29734 11.7027 9.17027 14.0706 9.40706L15 9.5V10.5L14.0706 10.5929C11.7027 10.8297 9.82973 12.7027 9.59294 15.0706L9.5 16H8.5L8.40706 15.0706C8.17027 12.7027 6.29734 10.8297 3.92939 10.5929L3 10.5V9.5L3.92939 9.40706C6.29734 9.17027 8.17027 7.29734 8.40706 4.92939Z"
      fill="currentColor"
    />
  </svg>
);

export const PlusIcon = ({ size = 16,currentColor}: { size?: number,currentColor:string }) => (
  <svg
    height={size}
    strokeLinejoin="round"
    viewBox="0 0 16 16"
    width={size}
    style={{ color: currentColor }}
  >
    <path
      fillRule="evenodd"
      clipRule="evenodd"
      d="M8.75 1.75V1H7.25V1.75V6.75H2.25H1.5V8.25H2.25H7.25V13.25V14H8.75V13.25V8.25H13.75H14.5V6.75H13.75H8.75V1.75Z"
      fill="currentColor"
    />
  </svg>
);

export const ArrowUpIcon = ({ size = 16 }: { size?: number }) => {
  return (
    <svg
      height={size}
      strokeLinejoin="round"
      viewBox="0 0 16 16"
      width={size}
      style={{ color: 'currentcolor' }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M8.70711 1.39644C8.31659 1.00592 7.68342 1.00592 7.2929 1.39644L2.21968 6.46966L1.68935 6.99999L2.75001 8.06065L3.28034 7.53032L7.25001 3.56065V14.25V15H8.75001V14.25V3.56065L12.7197 7.53032L13.25 8.06065L14.3107 6.99999L13.7803 6.46966L8.70711 1.39644Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const ChevronLeftIcon = ({ size = 16, currentColor = "currentcolor" }: { size?: number, currentColor?: string }) => {
  return (
    <svg 
      height={size} 
      width={size} 
      viewBox="0 0 24 24" 
      style={{ color: currentColor }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M15.41 7.41L14 6L8 12L14 18L15.41 16.59L10.83 12L15.41 7.41Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const ChevronRightIcon = ({ size = 16, currentColor = "currentcolor" }: { size?: number, currentColor?: string }) => {
  return (
    <svg 
      height={size} 
      width={size} 
      viewBox="0 0 24 24" 
      style={{ color: currentColor }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M10 6L8.59 7.41L13.17 12L8.59 16.59L10 18L16 12L10 6Z"
        fill="currentColor"
      />
    </svg>
  );
};

export const ArrowBackIcon = ({ size = 16, currentColor = "currentcolor" }: { size?: number, currentColor?: string }) => {
  return (
    <svg 
      height={size} 
      width={size} 
      viewBox="0 0 24 24" 
      style={{ color: currentColor }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"
        fill="currentColor"
      />
    </svg>
  );
};

export const SettingsIcon = ({ size = 16, currentColor = "currentcolor" }: { size?: number, currentColor?: string }) => {
  return (
    <svg 
      height={size} 
      width={size} 
      viewBox="0 0 24 24" 
      style={{ color: currentColor }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58c.18-.14.23-.41.12-.61l-1.92-3.32c-.12-.22-.37-.29-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96c-.22-.08-.47 0-.59.22L2.74 8.87c-.12.21-.08.47.12.61l2.03 1.58c-.05.3-.09.63-.09.94s.02.64.07.94l-2.03 1.58c-.18.14-.23.41-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6c-1.98 0-3.6-1.62-3.6-3.6s1.62-3.6 3.6-3.6 3.6 1.62 3.6 3.6-1.62 3.6-3.6 3.6z"
        fill="currentColor"
      />
    </svg>
  );
};

export const GitHubIcon = ({ size = 16, currentColor = "currentcolor" }: { size?: number, currentColor?: string }) => {
  return (
    <svg 
      height={size} 
      width={size} 
      viewBox="0 0 24 24" 
      style={{ color: currentColor }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.166 6.839 9.489.5.092.682-.217.682-.482 0-.237-.008-.866-.013-1.7-2.782.603-3.369-1.34-3.369-1.34-.454-1.156-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.087 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.268 2.75 1.026A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.026 2.747-1.026.546 1.377.202 2.394.1 2.647.64.7 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.161 22 16.416 22 12c0-5.523-4.477-10-10-10z"
        fill="currentColor"
      />
    </svg>
  );
};

export const SlackIcon = ({ size = 16, currentColor = "currentcolor" }: { size?: number, currentColor?: string }) => {
  return (
    <svg 
      height={size} 
      width={size} 
      viewBox="0 0 24 24" 
      style={{ color: currentColor }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M19.82 10.42c.18 0 .35 0 .53.06.86.2 1.4 1.06 1.2 1.92-.14.67-.75 1.18-1.41 1.24a4.05 4.05 0 01-.48 0 1.33 1.33 0 01-.62-.18 1.37 1.37 0 01-.71-1.25c0-.07 0-.14.03-.22.17-.95.65-1.57 1.46-1.57zm-6.26-6.2c.18 0 .36.01.54.05.86.19 1.41 1.04 1.21 1.9a1.53 1.53 0 01-1.48 1.09c-.15 0-.29 0-.42-.03a1.42 1.42 0 01-1.14-1.73c.17-.95.65-1.28 1.3-1.28zm-7.94 7.05c.85.19 1.4 1.05 1.2 1.9a1.6 1.6 0 01-.54.86c-.24.18-.54.27-.87.27-.12 0-.24 0-.36-.03a1.42 1.42 0 01-1.13-1.73c.14-.79.6-1.28 1.36-1.28.1.01.22.01.34.01zm10.85-2.12c.86.18 1.41 1.05 1.2 1.9a1.54 1.54 0 01-1.48 1.1h-.42a1.42 1.42 0 01-1.14-1.73c.18-.86 1.04-1.4 1.9-1.2 0-.07-.06-.07-.06-.07zM10.49 3c.86.19 1.41 1.05 1.2 1.9a1.54 1.54 0 01-1.48 1.1h-.42A1.42 1.42 0 018.65 4.3c.14-.8.6-1.3 1.37-1.3h.47zm-7.05 7.05a1.57 1.57 0 012.23.73 1.42 1.42 0 01-1.13 1.73h-.42a1.42 1.42 0 01-1.14-1.73c.12-.43.28-.67.46-.73zM15.06 8.6c.85.19 1.4 1.05 1.2 1.9a1.42 1.42 0 01-1.14 1.18h-.36a1.4 1.4 0 01-1.2-1.7c.19-.86 1.06-1.4 1.92-1.2.04-.18-.18-.18-.42-.18zM7.17 16.8c.86.2 1.4 1.06 1.2 1.92-.13.67-.74 1.18-1.4 1.24-.19.02-.36.02-.54.01a1.42 1.42 0 01-1.14-1.73c.19-.86 1.06-1.4 1.91-1.2 0-.24-.03-.24-.03-.24zm10.85-2.24c.85.19 1.4 1.05 1.2 1.9a1.42 1.42 0 01-1.13 1.2h-.36A1.42 1.42 0 0116.6 16c.19-.87 1.05-1.41 1.9-1.22 0-.22-.48-.22-.48-.22zM10.6 17.7c.86.19 1.4 1.05 1.2 1.9a1.54 1.54 0 01-1.47 1.1c-.13 0-.25 0-.35-.02a1.42 1.42 0 01-1.14-1.73c.18-.86 1.04-1.41 1.9-1.2l-.14-.05z"
        fill="currentColor"
      />
    </svg>
  );
};

export const JiraIcon = ({ size = 16, currentColor = "currentcolor" }: { size?: number, currentColor?: string }) => {
  return (
    <svg 
      height={size} 
      width={size} 
      viewBox="0 0 24 24" 
      style={{ color: currentColor }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M11.53 2c-.81.81-1.53 1.81-2.13 2.91L9.47 5l-3.44 3.44a.58.58 0 00-.06.06c-1.85 1.85-1.85 4.85 0 6.7.16.16.34.32.53.47 0 0 0 .03.03.03 1.95 1.53 4.75 1.5 6.66-.1l3.59-3.59v-.06c.19-.16.37-.32.53-.47 1.82-1.82 1.85-4.76.07-6.63l-.07-.07L14.1 2H11.53zm.5 5.44c-.81.81-1.5 1.69-2.03 2.66a6.7 6.7 0 00-.5.97h.03c-.53 1.24-.59 2.63-.19 3.91.13.42.31.82.56 1.19-.72-.06-1.4-.31-1.98-.72a.23.23 0 00-.03-.03c-.13-.09-.25-.22-.37-.34a3.38 3.38 0 1147.9-4.78l2.35-2.35a6.27 6.27 0 00-.87-3.15A6.3 6.3 0 0014.41 2h-.19l-2.2 2.2v3.24h.01zm2.5 1.53c.72-.72 1.35-1.53 1.88-2.38a3.38 3.38 0 01-.15 4.13c-.1.12-.21.24-.34.34a3.38 3.38 0 01-4.41.28 4.63 4.63 0 01.28-1.16v-.03c.47-.91 1.1-1.72 1.85-2.44l.9-.75v2.01h-.01z"
        fill="currentColor"
      />
    </svg>
  );
};

export const TrashIcon = ({ size = 16, currentColor = "currentcolor" }: { size?: number, currentColor?: string }) => {
  return (
    <svg 
      height={size} 
      width={size} 
      viewBox="0 0 24 24" 
      style={{ color: currentColor }}
    >
      <path
        fillRule="evenodd"
        clipRule="evenodd"
        d="M16 9v10H8V9h8m-1.5-6h-5l-1 1H5v2h14V4h-3.5l-1-1zM18 7H6v12c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7z"
        fill="currentColor"
      />
    </svg>
  );
};
