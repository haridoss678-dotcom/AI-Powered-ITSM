import { Link, useParams } from 'react-router-dom';
import TicketDetailsPanel from '../components/TicketDetailsPanel';

export default function DashboardTicketDetailsPage() {
  const { ticketId } = useParams();

  return (
    <section className="panel">
      <p className="eyebrow">Operations view</p>
      <div className="section-heading">
        <h2>Ticket details</h2>
        <Link className="secondary-button" to="/dashboard">Back to dashboard</Link>
      </div>
      <TicketDetailsPanel ticketId={ticketId} allowUpdates />
    </section>
  );
}
