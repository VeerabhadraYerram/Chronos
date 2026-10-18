export const COMPANY_QUESTION_GUIDANCE =
  'Ask about company knowledge—decisions, policies, clients, operations, or who owns what. For example: “How many clients do we have?”';

// Input guidance only; company questions still go to the graph investigator.
export function questionInputHint(text) {
  const question = text.trim();
  if (question.length > 1500) return 'Please keep your question under 1,500 characters.';
  if (question.length < 3 || /^(?:hi|hello|hey|hiya|hello there|hi there|hey there|good morning|good afternoon|good evening)[\s!?.]*$/iu.test(question)) {
    return COMPANY_QUESTION_GUIDANCE;
  }
  return '';
}
