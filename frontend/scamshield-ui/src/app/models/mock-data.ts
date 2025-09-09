import { ChecklistItem, RecipientIntel, RiskAssessment, TransactionDetails, UserPatternSummary } from './models';


export const tx: TransactionDetails = {
fromAccount: 'Main Checking •••• 3878',
toRecipient: 'Global Tech Solutions Ltd.',
iban: 'DE44 5001 0517 5407 3249 31',
amount: 2450,
currency: 'USD',
date: new Date().toISOString(),
reference: 'Software Services',
type: 'vendor',
device: 'Chrome on Windows',
location: 'Bucharest, RO'
};


export const recipient: RecipientIntel = {
name: 'Global Tech Solutions Ltd.',
cui: 'HRB 112233',
address: 'Friedrichstraße 12, Berlin',
incorporated: '2019-03-11',
reputation: 'unverified',
previousTx: 0,
flags: ['New recipient', 'Limited online presence']
};


export const pattern: UserPatternSummary = {
typicalAvg: 750,
largest: 1200,
current: tx.amount,
history: [300, 420, 500, 760, 400, 900, 650, 1200, 380, 2450]
};


export const assessment: RiskAssessment = {
overall: 'medium',
scorePct: 65,
reasons: [
{ icon: '👤', title: 'New recipient', desc: 'First time paying this account' },
{ icon: '💸', title: 'Unusual amount', desc: 'Much higher than typical transfers' },
{ icon: '🔎', title: 'Invoice format risk', desc: 'Reference contains common scam pattern' }
],
bars: [
{ name: 'Amount Risk', value: 75 },
{ name: 'Recipient Risk', value: 60 },
{ name: 'Pattern Risk', value: 80 },
{ name: 'Time Risk', value: 35 }
]
};


export const checklist: ChecklistItem[] = [
{ key: 'verifyId', label: 'I know the recipient and verified their identity', checked: false },
{ key: 'similarTx', label: 'I have made similar transactions before', checked: false },
{ key: 'understand', label: 'I understand the purpose of this transaction', checked: false },
{ key: 'pressure', label: 'I am not being pressured or rushed to make this payment', checked: false },
{ key: 'irreversible', label: 'I understand wire transfers cannot typically be reversed', checked: false }
];